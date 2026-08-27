#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""understand.py — 把一段 git diff 变成 Claude 风格的 code-review 网页。

用法：
  python3 understand.py scan   [--base <ref>] [--out <dir>]   # 扫描变更，生成 data.json + annotations 骨架
  python3 understand.py render [--out <dir>]                   # 用 data.json + annotations.json 渲染 report.html

流程：
  1. scan  — 解析 `git diff` 统一 diff，写 <out>/data.json（结构化变更）与 <out>/annotations.json（若不存在则写空骨架）。
  2. Claude 编辑 <out>/annotations.json，为关键代码段补「相关单位需求」与「代码解释」。
  3. render — 合并 data.json + annotations.json，把结果注入 template.html，写 <out>/report.html。

只依赖 Python 标准库；不联网（Prism.js 走 CDN，在浏览器里加载）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "template.html")

# 扩展名 → Prism 语言标识
LANG_MAP = {
    "java": "java", "kt": "kotlin", "kts": "kotlin", "scala": "scala", "groovy": "groovy",
    "py": "python", "rb": "ruby", "go": "go", "rs": "rust",
    "js": "javascript", "jsx": "jsx", "ts": "typescript", "tsx": "tsx", "mjs": "javascript",
    "c": "c", "h": "c", "cpp": "cpp", "cc": "cpp", "hpp": "cpp", "cs": "csharp",
    "php": "php", "swift": "swift", "m": "objectivec",
    "sql": "sql", "sh": "bash", "bash": "bash", "zsh": "bash",
    "html": "markup", "xml": "markup", "vue": "markup", "svg": "markup",
    "css": "css", "scss": "scss", "less": "less",
    "json": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml", "ini": "ini",
    "md": "markdown", "markdown": "markdown", "proto": "protobuf", "gradle": "groovy",
    "dockerfile": "docker", "makefile": "makefile",
}


def sh(args, cwd=None):
    """跑一个命令，返回 stdout（文本）。失败时返回空串而不抛异常，便于降级。"""
    # git：关掉 core.quotepath，避免中文/非 ASCII 路径被转义成八进制。
    if args and args[0] == "git":
        args = ["git", "-c", "core.quotepath=false"] + args[1:]
    try:
        out = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, check=False)
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def repo_root():
    root = sh(["git", "rev-parse", "--show-toplevel"]).strip()
    return root or os.getcwd()


def detect_base(root, explicit):
    """决定 diff 基线。默认与主分支的 merge-base（回退 HEAD）。"""
    if explicit:
        return explicit
    # 找主分支
    for cand in ("origin/main", "main", "origin/master", "master"):
        if sh(["git", "rev-parse", "--verify", "--quiet", cand], cwd=root).strip():
            mb = sh(["git", "merge-base", "HEAD", cand], cwd=root).strip()
            if mb:
                return mb
    return "HEAD"


def lang_for(path):
    name = os.path.basename(path).lower()
    if name in ("dockerfile", "makefile"):
        return LANG_MAP[name]
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return LANG_MAP.get(ext, "none")


def collect_diff(root, base, pathspecs=None):
    """收集三部分变更并合并：已提交(base..HEAD) + 已暂存 + 未暂存 + 未跟踪。

    返回统一 diff 文本列表；对未跟踪文件用 --no-index 生成新增 diff。
    pathspecs：可选 git pathspec 列表，仅限定这些路径。
    """
    pathspecs = list(pathspecs or [])
    diffs = []
    # 已跟踪：base 到工作区（含已/未暂存），一次 diff 覆盖
    diffs.append(sh(["git", "diff", "--no-color", "-M", base, "--"] + pathspecs, cwd=root))
    # 未跟踪文件：逐个 --no-index 生成「全新增」diff
    untracked = sh(["git", "ls-files", "--others", "--exclude-standard", "--"] + pathspecs, cwd=root)
    for rel in filter(None, (l.strip() for l in untracked.splitlines())):
        d = sh(["git", "diff", "--no-color", "--no-index", "--", os.devnull, rel], cwd=root)
        if d:
            diffs.append(d)
    return "\n".join(d for d in diffs if d.strip())


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def parse_diff(text):
    """把统一 diff 解析成文件列表结构。"""
    files = []
    cur = None
    old_no = new_no = 0
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("diff --git"):
            cur = {"path": "", "old_path": "", "status": "M", "binary": False,
                   "hunks": [], "additions": 0, "deletions": 0}
            files.append(cur)
            # 从 a/... b/... 提取路径（先给个初值，后续 +++/rename 覆盖）
            m = re.match(r"diff --git a/(.*) b/(.*)$", line)
            if m:
                cur["old_path"] = m.group(1)
                cur["path"] = m.group(2)
            i += 1
            continue
        if cur is None:
            i += 1
            continue
        if line.startswith("new file"):
            cur["status"] = "A"
        elif line.startswith("deleted file"):
            cur["status"] = "D"
        elif line.startswith("rename from"):
            cur["status"] = "R"
            cur["old_path"] = line[len("rename from "):].strip()
        elif line.startswith("rename to"):
            cur["path"] = line[len("rename to "):].strip()
        elif line.startswith("Binary files") or line.startswith("GIT binary patch"):
            cur["binary"] = True
        elif line.startswith("--- "):
            p = line[4:].strip()
            if p != "/dev/null":
                cur["old_path"] = p[2:] if p.startswith(("a/", "b/")) else p
        elif line.startswith("+++ "):
            p = line[4:].strip()
            if p == "/dev/null":
                cur["status"] = "D"
            else:
                cur["path"] = p[2:] if p.startswith(("a/", "b/")) else p
        elif line.startswith("@@"):
            m = HUNK_RE.match(line)
            if not m:
                i += 1
                continue
            old_no = int(m.group(1))
            new_no = int(m.group(3))
            hunk = {"header": line, "context": (m.group(5) or "").strip(), "lines": []}
            cur["hunks"].append(hunk)
            i += 1
            # 消费 hunk 体
            while i < n:
                bl = lines[i]
                if bl.startswith("@@") or bl.startswith("diff --git"):
                    break
                if bl.startswith("\\"):  # \ No newline at end of file
                    i += 1
                    continue
                tag = bl[:1]
                text_line = bl[1:]
                if tag == "+":
                    hunk["lines"].append({"type": "add", "oldNo": None, "newNo": new_no, "text": text_line})
                    new_no += 1
                    cur["additions"] += 1
                elif tag == "-":
                    hunk["lines"].append({"type": "del", "oldNo": old_no, "newNo": None, "text": text_line})
                    old_no += 1
                    cur["deletions"] += 1
                else:  # 上下文行（含空行，空行的 tag 是空格）
                    hunk["lines"].append({"type": "ctx", "oldNo": old_no, "newNo": new_no, "text": text_line})
                    old_no += 1
                    new_no += 1
                i += 1
            continue
        i += 1
    # 规整路径与语言
    for f in files:
        if not f["path"] and f["old_path"]:
            f["path"] = f["old_path"]
        f["language"] = lang_for(f["path"])
    # 丢掉既无 hunk 又非二进制的空壳（纯 mode change 等）
    return [f for f in files if f["hunks"] or f["binary"]]


def cmd_scan(args):
    root = repo_root()
    base = detect_base(root, args.base)
    out = args.out
    os.makedirs(out, exist_ok=True)

    diff_text = collect_diff(root, base, args.path)
    files = parse_diff(diff_text)

    base_short = sh(["git", "rev-parse", "--short", base], cwd=root).strip() or base
    branch = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root).strip()

    data = {
        "title": "代码变更审阅 · " + (branch or os.path.basename(root)),
        "summary": "",
        "base": base_short,
        "branch": branch,
        "generatedAt": args.now or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "files": [
            {
                "path": f["path"],
                "oldPath": f["old_path"],
                "status": f["status"],
                "language": f["language"],
                "binary": f["binary"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "hunks": f["hunks"],
            }
            for f in files
        ],
    }
    with open(os.path.join(out, "data.json"), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)

    # annotations 骨架：仅在不存在时创建，避免覆盖 Claude 已写内容
    ann_path = os.path.join(out, "annotations.json")
    if not os.path.exists(ann_path):
        skeleton = {
            "title": data["title"],
            "summary": "",
            "files": [
                {"path": f["path"], "summary": "", "annotations": []}
                for f in data["files"]
            ],
        }
        with open(ann_path, "w", encoding="utf-8") as fp:
            json.dump(skeleton, fp, ensure_ascii=False, indent=2)
        ann_created = True
    else:
        ann_created = False

    print(json.dumps({
        "ok": True,
        "root": root,
        "base": base_short,
        "files": len(data["files"]),
        "additions": sum(f["additions"] for f in data["files"]),
        "deletions": sum(f["deletions"] for f in data["files"]),
        "data": os.path.join(out, "data.json"),
        "annotations": ann_path,
        "annotationsCreated": ann_created,
        "paths": [f["path"] for f in data["files"]],
    }, ensure_ascii=False, indent=2))


def cmd_render(args):
    out = args.out
    data_path = os.path.join(out, "data.json")
    if not os.path.exists(data_path):
        print("错误：找不到 %s，请先运行 scan。" % data_path, file=sys.stderr)
        sys.exit(1)
    with open(data_path, encoding="utf-8") as fp:
        data = json.load(fp)

    ann_path = os.path.join(out, "annotations.json")
    if os.path.exists(ann_path):
        with open(ann_path, encoding="utf-8") as fp:
            ann = json.load(fp)
        if ann.get("title"):
            data["title"] = ann["title"]
        if ann.get("summary"):
            data["summary"] = ann["summary"]
        by_path = {f.get("path"): f for f in ann.get("files", [])}
        for f in data["files"]:
            a = by_path.get(f["path"])
            if not a:
                continue
            f["summary"] = a.get("summary", "")
            f["annotations"] = a.get("annotations", [])

    with open(TEMPLATE, encoding="utf-8") as fp:
        template = fp.read()
    payload = json.dumps(data, ensure_ascii=False)
    # 避免 JSON 里的 </script> 提前闭合脚本块
    payload = payload.replace("</", "<\\/")
    html = template.replace("__UNDERSTAND_PAYLOAD__", payload)

    report = os.path.join(out, "report.html")
    with open(report, "w", encoding="utf-8") as fp:
        fp.write(html)
    print(json.dumps({"ok": True, "report": os.path.abspath(report),
                      "files": len(data["files"])}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="Claude 风格 code-review 网页生成器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan", help="解析 git diff，生成 data.json + annotations 骨架")
    sp.add_argument("--base", default="", help="diff 基线 ref（默认与主分支 merge-base）")
    sp.add_argument("--out", default=".understand", help="输出目录（默认 .understand）")
    sp.add_argument("--now", default="", help="固定生成时间戳（可选）")
    sp.add_argument("--path", action="append", default=[],
                    help="仅限定这些 git pathspec（可多次），如 ':(glob)**/pwa/**'")
    sp.set_defaults(func=cmd_scan)

    rp = sub.add_parser("render", help="合并注释并渲染 report.html")
    rp.add_argument("--out", default=".understand", help="输出目录（默认 .understand）")
    rp.set_defaults(func=cmd_render)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
