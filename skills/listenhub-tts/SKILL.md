---
name: listenhub-tts
description: >
  使用 ListenHub API 将文本转换为语音（TTS）。支持三种模式：快速合成（/v1/tts）、
  多角色脚本（/v1/speech）、长文本流式合成（/v1/flow-speech/episodes）。
  音色未指定时自动获取音色列表供用户选择，默认使用 chat-girl-105-cn（晓曼）。
  Use when user says: "tts", "text to speech", "语音合成", "文字转语音", "朗读",
  "生成语音", "生成音频", "转音频", "text to audio"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
user-invocable: true
metadata:
  trigger: TTS语音合成、text to speech、文字转语音、朗读文本、生成音频
---

# ListenHub TTS: 文本转语音

使用 ListenHub OpenAPI 将文本转换为语音。支持三种合成模式，覆盖从短文本到长文本的全场景。

## API 信息

- **Base URL:** `https://api.marswave.ai/openapi`
- **认证:** `Authorization: Bearer $LISTENHUB_API_KEY`（从环境变量读取）
- **前置检查:** 调用任何 API 前先确认 `LISTENHUB_API_KEY` 环境变量已设置，未设置则提示用户配置

## 音色选择流程

### 用户已明确指定音色

直接使用用户指定的 speakerId，跳过选择流程。

### 用户未指定音色

1. 调用 `GET /v1/speakers/list?language=zh` 获取可用音色列表
2. 按 AskUserQuestion 展示音色列表供用户选择，格式如下：
   - 默认选中 `chat-girl-105-cn`（晓曼 dxqqq）
   - 列表展示：`{name}（{gender}，{speakerId}）`
   - 附带每个音色的 demoAudioUrl 供参考
3. 用户确认后使用选定的 speakerId

### 默认音色

| 字段 | 值 |
|------|-----|
| speakerId | `chat-girl-105-cn` |
| 名称 | 晓曼 dxqqq |

## 三种合成模式

### 模式一：快速合成（短文本，单音色）

**适用场景：** 短文本（< 1000 字），单音色，需要低延迟

**接口：** `POST /v1/tts`

**请求体：**

```json
{
  "text": "要合成的文本",
  "speakerId": "chat-girl-105-cn",
  "format": "mp3",
  "sampleRate": 24000,
  "speed": 1.0
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要合成的文本 |
| speakerId | string | 是 | 音色 ID |
| format | string | 否 | 输出格式，默认 `mp3` |
| sampleRate | int | 否 | 采样率，默认 `24000` |
| speed | float | 否 | 语速，默认 `1.0`，范围 `0.5 ~ 2.0` |

**响应：** 直接返回 MP3 二进制流（`Content-Type: audio/mpeg`）

**调用示例：**

```bash
curl -X POST "https://api.marswave.ai/openapi/v1/tts" \
  -H "Authorization: Bearer $LISTENHUB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "speakerId": "chat-girl-105-cn"}' \
  -o output.mp3
```

### 模式二：多角色脚本合成

**适用场景：** 多角色对话、播客、有声书片段，需要不同音色交替朗读

**接口：** `POST /v1/speech`

**请求体：**

```json
{
  "script": [
    {
      "text": "你好，欢迎收听本期节目。",
      "speakerId": "chat-girl-105-cn"
    },
    {
      "text": "谢谢，今天我们来聊聊 AI。",
      "speakerId": "chat-boy-101-cn"
    }
  ],
  "format": "mp3",
  "sampleRate": 24000
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| script | array | 是 | 脚本数组，每项包含 text 和 speakerId |
| script[].text | string | 是 | 该段文本 |
| script[].speakerId | string | 是 | 该段的音色 ID |
| format | string | 否 | 输出格式，默认 `mp3` |
| sampleRate | int | 否 | 采样率，默认 `24000` |

**响应：** JSON

```json
{
  "audioUrl": "https://cdn.example.com/output.mp3",
  "duration": 12.5
}
```

**调用示例：**

```bash
curl -X POST "https://api.marswave.ai/openapi/v1/speech" \
  -H "Authorization: Bearer $LISTENHUB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "script": [
      {"text": "你好，欢迎收听。", "speakerId": "chat-girl-105-cn"},
      {"text": "谢谢，我们开始吧。", "speakerId": "chat-boy-101-cn"}
    ]
  }'
```

### 模式三：长文本流式合成

**适用场景：** 长文本（> 1000 字），文章朗读，需要 AI 润色或分段处理

**接口：** `POST /v1/flow-speech/episodes`

**请求体：**

```json
{
  "title": "文章标题",
  "content": "长文本内容...",
  "speakerId": "chat-girl-105-cn",
  "mode": "direct",
  "format": "mp3"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 音频标题 |
| content | string | 否 | 文本内容（与 contentUrl 二选一） |
| contentUrl | string | 否 | 内容 URL（与 content 二选一） |
| speakerId | string | 是 | 音色 ID |
| mode | string | 否 | `direct`（直接合成）或 `aiPolish`（AI 润色），默认 `direct` |
| format | string | 否 | 输出格式，默认 `mp3` |

**响应：** JSON

```json
{
  "episodeId": "ep_abc123",
  "status": "processing"
}
```

**轮询获取结果：**

```bash
GET /v1/flow-speech/episodes/{episodeId}
```

**轮询策略：**
1. 提交后等待 30 秒
2. 之后每 10 秒轮询一次
3. 直到 status 变为 `completed` 或 `failed`

**轮询响应：**

```json
{
  "episodeId": "ep_abc123",
  "status": "completed",
  "audioUrl": "https://cdn.example.com/output.mp3",
  "duration": 180.5
}
```

| status 值 | 说明 |
|-----------|------|
| processing | 合成中，继续轮询 |
| completed | 合成完成，audioUrl 可用 |
| failed | 合成失败，查看 errorMessage |

**调用示例：**

```bash
# 提交任务
curl -X POST "https://api.marswave.ai/openapi/v1/flow-speech/episodes" \
  -H "Authorization: Bearer $LISTENHUB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI 技术趋势",
    "content": "长文本内容...",
    "speakerId": "chat-girl-105-cn",
    "mode": "direct"
  }'

# 轮询结果
curl "https://api.marswave.ai/openapi/v1/flow-speech/episodes/ep_abc123" \
  -H "Authorization: Bearer $LISTENHUB_API_KEY"
```

## 音色列表查询

**接口：** `GET /v1/speakers/list`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| language | string | 否 | 筛选语言，如 `zh`（中文）、`en`（英文） |

**响应：**

```json
{
  "speakers": [
    {
      "name": "晓曼 dxqqq",
      "speakerId": "chat-girl-105-cn",
      "demoAudioUrl": "https://cdn.example.com/demo.mp3",
      "gender": "female",
      "language": "zh"
    }
  ]
}
```

## 模式选择逻辑

根据用户输入自动选择最合适的模式：

| 条件 | 模式 |
|------|------|
| 文本 ≤ 1000 字，单音色 | 模式一：`/v1/tts` |
| 多角色脚本，需要不同音色 | 模式二：`/v1/speech` |
| 文本 > 1000 字，或需要 AI 润色 | 模式三：`/v1/flow-speech/episodes` |
| 用户提供 URL 作为内容来源 | 模式三：`/v1/flow-speech/episodes` |

如果用户明确指定模式，优先使用用户指定的模式。

## 用户交互

### 音色选择

当用户未指定音色时，使用 AskUserQuestion 展示音色列表：

```
请选择音色（默认：晓曼 dxqqq）：
A. 晓曼 dxqqq（女，chat-girl-105-cn）[默认]
B. [其他音色名称]（[性别]，[speakerId]）
C. ...
```

### 合成参数

可选询问：
- 语速 speed（默认 1.0）
- 输出格式 format（默认 mp3）
- 长文本模式：direct 还是 aiPolish（默认 direct）
- 输出文件路径（默认 `./output.mp3`）

## 输出

1. 将音频保存到指定路径（默认 `./output.mp3`）
2. 输出合成摘要：
   - 使用的模式
   - 音色名称和 ID
   - 音频时长
   - 文件大小
   - 文件路径

## 错误处理

- **401 Unauthorized:** 提示用户检查 `LISTENHUB_API_KEY` 环境变量
- **400 Bad Request:** 检查请求参数，向用户报告具体错误
- **flow-speech failed:** 报告 errorMessage，建议用户重试或切换模式
- **网络错误:** 提示检查网络连接，建议重试

## 完整示例

**用户输入：** "把这段文字转成语音：今天天气真好，适合出去散步。"

**执行流程：**
1. 检查 `LISTENHUB_API_KEY` ✓
2. 文本长度 < 1000 字，单音色 → 选择模式一 `/v1/tts`
3. 用户未指定音色 → 默认使用 `chat-girl-105-cn`（晓曼）
4. 调用 API 合成
5. 保存到 `./output.mp3`
6. 输出摘要

**用户输入：** "用晓曼的声音朗读这篇文章：article.md"

**执行流程：**
1. 读取 `article.md` 内容
2. 检查文本长度 > 1000 字 → 选择模式三 `/v1/flow-speech/episodes`
3. 音色已指定：`chat-girl-105-cn`（晓曼）
4. 提交合成任务
5. 轮询直到完成
6. 下载音频保存到 `./article.mp3`
7. 输出摘要
