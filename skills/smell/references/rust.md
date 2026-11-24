# Rust Language Profile

Language layer for the `smell` skill. Load this file when the target is a Rust codebase (a Cargo workspace or a single crate); the language-agnostic heuristics in [`../SKILL.md`](../SKILL.md) still apply.

Everything here is a **candidate signal**, exactly like the generic tables: a `.clone()`, an `unwrap()`, or a nesting depth is never a finding until you have read the surrounding code, its callers, and its runtime path. Where this profile differs from the generic heuristics is in three places: the evidence commands are Cargo-native, the candidate families are Rust-specific (ownership, panics, async), and the false-positive controls matter more because the compiler already enforces many invariants that the generic heuristics assume a human maintains.

---

## 1. Establish the Baseline

Run these before forming any finding. They decide what "module", "layer", and "hot path" mean for this project.

| Command | What it establishes | Limits |
|---------|--------------------|--------|
| `cargo metadata --format-version 1 --no-deps` | Workspace members, targets (`lib`/`bin`/`test`/`bench`/`example`), editions, dependency names | Requires a working toolchain; does not read source |
| `cargo tree --workspace --edges normal` | Runtime dependency graph for layer-boundary checks | Resolved graph only, not actual use |
| `cargo tree --workspace --duplicates` | Duplicate versions of the same crate | A duplicate is a cost signal, not automatically a smell |
| `cargo tree -e features -i <crate>` | Which features pull a dependency in | Feature unification is not intent |
| `cargo test --workspace --no-run` | Whether the tests still compile | Slow on large workspaces; skip if it dominates the run |
| `git log --since='6 months ago' --name-only --pretty=format: \| sort \| uniq -c \| sort -rn \| head -40` | Change frequency per file, for Shotgun Surgery / Divergent Change evidence | History is context, not proof of a design defect |

Read `Cargo.toml` (`[workspace]`, `[dependencies]`, `[dev-dependencies]`, `[features]`, `[profile.*]`) and `rust-toolchain.toml` when present. The edition (2015/2018/2021/2024) and the toolchain gate which idioms are even available, and the report should name the baseline it assumed.

`build.rs`, `xtask/`, proc-macro crates, and `#[cfg(test)]` code are separate populations: do not mix their metrics with runtime source.

The clippy lint names and groups quoted in sections 3, 4, 5, 6, and 9 were checked against clippy 0.1.100 (Rust 1.100.0 stable). Lints move between groups across releases, so re-check with `cargo clippy -- -W help` before turning any of them into a CI gate.

---

## 2. Workspace and Boundary Smells

| Smell | Detection heuristic | Typical remedy |
|-------|--------------------|----------------|
| Business logic in the binary target | `src/main.rs` or `src/bin/*.rs` holds domain types, SQL, HTTP handlers, or > ~200 lines while the library crate only re-exports | Move logic into the `lib` crate; keep binaries as argument parsing and wiring |
| Layer leak | A domain/application crate depends on `sqlx`, `diesel`, `axum`, `actix-web`, `reqwest`, `tonic`; test-only helpers live in `[dependencies]` instead of `[dev-dependencies]` | Push I/O into adapter crates that depend inward |
| God module | One module > ~500 lines **and** > ~20 public items, or a `lib.rs` that is simultaneously the `pub use` surface and the implementation | Split by responsibility; keep `lib.rs` as an export list |
| Feature-flag combinatorial | Many `#[cfg(feature = "...")]` variants of the same function, or features that must be enabled together with no `foo = ["bar"]`/`foo = ["dep:bar"]` edge declaring that requirement | Declare the feature edge, or split crates |
| Over-wide `pub` surface | Items marked `pub` with no use outside the crate while `pub(crate)` is unused; blanket `#[allow(unused_imports)]` around re-exports | Narrow visibility, re-export deliberately |
| Suppression instead of fix | Crate-level `#![allow(dead_code)]`, `#![allow(clippy::all)]`, `#[allow(unused)]` on whole modules | Fix the item, or scope the allowance to one item with a reason comment |
| Duplicate versions | `cargo tree --duplicates` reporting two majors of a core crate | Align versions; weigh compile time and binary size |

**Cycle reporting.** Cargo rejects cycles between normal and build dependencies, so an import graph built from those edges cannot contain a crate cycle; cycles introduced through `dev-dependencies` are legal. Module cycles inside a crate are legal and usually harmless. Report a cycle only when it reveals a reversed design boundary (for example a `domain` module importing `infra` items back), and cite the boundary violation instead of a graph mechanic.

---

## 3. Ownership and Borrowing

These are Rust's native coupling smells. Each needs the surrounding function read: a clone that ends a borrow conflict on a collection is different from a clone of a small `Copy` type.

### Clone to satisfy the borrow checker

- **Detection:** `.clone()`, `.to_owned()`, `.to_vec()` on a non-`Copy` value (struct, `Vec`, `String`, map) at a mutable-borrow conflict, inside a loop, or on a whole collection passed to a read-only function. Count density per module as a candidate, then read the sites.
- **Remedy:** restructure ownership — borrow the smaller field, split the struct, `std::mem::take`, `Option::take`, `Cow<'_, T>`, or take `&[T]`/`&str` instead of an owned copy.
- **Not a smell:** `Arc::clone` is a refcount bump (still prefer `Arc::clone(&x)` over `x.clone()` for readability, which `clippy::clone_on_ref_ptr` can enforce); small `Copy` aggregates; a clone that exists to end a lock guard or an iterator borrow — verify the reason first.

### Interior-mutability sprawl

- **Detection:** `Rc<RefCell<T>>`, `Arc<Mutex<T>>`, `Arc<RwLock<T>>` as the default way to share state across many modules; `borrow_mut()` inside loops or nested calls where a runtime `BorrowMutError` is possible; `Arc<Mutex<HashMap<..>>>` acting as a global registry.
- **Remedy:** explicit `&mut` plumbing, ownership transfer, message passing (`std::sync::mpsc`, `tokio::sync::mpsc`), or one owner plus shared references.
- **Not a smell:** single-threaded UI/tree structures on `Rc<RefCell>`, short-lived caches, `OnceLock`/`LazyLock` for immutable initialization.

### Shared mutable state as architecture

- **Detection:** `static`/`lazy_static`/`OnceLock<Mutex<..>>` globals written from many modules, tests that must run serially, configuration or connection pools smuggled through globals.
- **Remedy:** pass an explicit context struct, injected at construction.
- This is the Rust form of **Common Coupling**: report it as Coupling, not as a separate Rust-only finding.

### `unsafe` without a contract

- **Detection:** `unsafe { }`, `unsafe fn`, `unsafe impl Send/Sync`, `transmute`, raw-pointer dereference. `clippy::undocumented_unsafe_blocks` and `clippy::multiple_unsafe_ops_per_block` (restriction group) turn missing or overloaded safety reasoning into a lint; `cargo geiger` gives per-crate counts when installed.
- **Confirm:** does each block state its invariant in a `// SAFETY:` comment, and is that invariant enforced by the surrounding type? `unsafe` in `-sys`/FFI wrappers with `#[repr(C)]` types is expected and usually fine.
- **Remedy:** encapsulate behind a safe newtype with documented invariants; drop `unsafe impl Send/Sync` unless the guarantee is proven.
- **Severity:** `unsafe` is not a smell by itself. Unsound `unsafe` (missing invariant, interior mutation behind a shared reference, `transmute` across incompatible layouts) is Critical when reachable.

### Inheritance emulation through `Deref`

- **Detection:** `impl Deref`/`impl DerefMut` on a type that is not a smart pointer or newtype wrapper, used so callers can reach the inner type's methods or fields.
- **Remedy:** explicit delegation, or `AsRef`/`Borrow` for borrowing conversions; composition methods for behavior.

### Lifetime over-parameterization

- **Detection:** explicit lifetimes on most public structs and functions, public APIs returning references into internal state, or `&'a self` methods that force callers into borrow gymnastics when elision or ownership would do.
- **Remedy:** own at the API boundary (`String`, `Arc<T>`, `Vec<T>`) and borrow internally.
- **Not a smell:** zero-copy parsers, serializers, and iterator adapters that are deliberately built around borrowed views.

---

## 4. Panics and Error Handling

### `unwrap`/`expect` on a reachable path

- **Detection:** `.unwrap()`, `.expect(`, `panic!`, `assert!`, `todo!`, `unimplemented!`, `unreachable!`, direct indexing `x[i]`, and slicing `&s[a..b]` outside test code. Exclude `#[cfg(test)]`, `tests/`, `benches/`, `examples/`, and `build.rs` unless the artifact ships.
- **Confirm:** is the failure reachable from user input, network data, files, or environment? If yes, report Critical (availability) with the input-to-site path. Guarding untrusted runtime input (network, file, user) with `assert!` instead of returning an error is a **Fail Fast** policy mismatch — report it once with the input path. Argument-contract assertions on a public API are idiomatic Rust: not a finding. If the `expect` merely restates a check the code performed immediately before (as after `if let Some(x) = ..`), it is a Suggestion or not a finding.
- **Remedy:** propagate with `?`, convert with `thiserror`, validate at the boundary, use `.get()` for untrusted indices.
- **Enablers:** `clippy::unwrap_used`, `clippy::expect_used`, `clippy::panic`, `clippy::indexing_slicing`, `clippy::todo`, and `clippy::unimplemented` live in the restriction group and are allow-by-default. Enable them individually (for example `cargo clippy -- -W clippy::unwrap_used`); do not blanket-enable the restriction group, and relax them inside test modules where panicking is the correct behavior.

### Error swallowing

- **Detection:** `let _ = fallible();`, `.ok()` on a `Result`, `.unwrap_or_default()` hiding a failure, `if let Ok(..)` without an `else`, `match` arms turning every `Err` into a default, `map_err(|_| ...)` dropping the source.
- **Remedy:** keep the source (`#[source]`/`#[from]`), log once at the boundary, or return the error to the caller.

### Type-erased and stringly-typed errors

- **Detection:** `Result<T, String>`, `Box<dyn Error>` in a library's public API, `anyhow::Error` in a library crate, `.to_string()` applied to errors before returning, error enums whose variants only wrap `String`.
- **Remedy:** a `thiserror` enum with typed variants and `#[source]`; `anyhow` only at binary/application edges, with `.context()`.

### Cast and numeric smells

- **Detection:** `as` between integer widths, `as usize`/`as u32` on untrusted lengths, `f32`/`f64` compared with `==` for identity or deduplication, a float wrapper whose hand-written `Eq`/`Hash` disagrees with its own `PartialEq` (NaN not reflexive, `0.0`/`-0.0` split, `to_bits` disagreeing with `==`) so it can key a map, `usize` in serialized formats or cross-platform protocols, arithmetic on values that can wrap silently in release.
- **Remedy:** `try_into()`, `checked_*`/`saturating_*` where overflow is possible, domain newtypes with validated constructors.

### Suppression-driven "green"

- **Detection:** crate-level `#![allow(clippy::all)]`, `#![allow(dead_code)]`, `#[allow(unused)]` on modules, `--cap-lints allow` applied to a workspace member, CI running clippy without `-D warnings` while the code depends on suppressions.
- **Remedy:** scope allowances to the item and state the reason; repeated cases become a process finding under **Fail Fast** or **KISS** rather than one finding per allowance.

---

## 5. Async and Concurrency

Only applies when the crate uses an async runtime; "async is used" is never a smell.

| Smell | Detection | Remedy |
|-------|-----------|--------|
| Blocking in async | `std::fs`, `std::thread::sleep`, `std::net`, `reqwest::blocking`, `Command::output` inside `async fn`; nested `block_on`; CPU-bound work without `spawn_blocking` | Move to `spawn_blocking`/a worker thread, or use the async API |
| Guard held across `.await` | `std::sync::MutexGuard`/`RwLockWriteGuard`/`RefMut` alive at an `.await` (serialization, potential deadlock). `clippy::await_holding_lock` sits in the `suspicious` group and warns by default; `clippy::await_holding_refcell_ref` covers the `RefCell` variant | Narrow the lock scope, or use `tokio::sync::Mutex` when the guard must cross an await |
| Detached tasks | `tokio::spawn`/`spawn_local` whose `JoinHandle` is dropped, no shutdown path, errors only logged at debug | Keep handles, supervise them, cancel on shutdown |
| Unbounded work | Unbounded channels/queues, `FuturesUnordered` growth without a cap, one task per item without a semaphore | Bounded channel plus `Semaphore`/`buffer_unordered(n)` |
| Missing limits | HTTP/DB calls without timeout, no `tower` timeout or load-shed layer, unbounded retries | Timeouts, retry budget, concurrency limit |
| Cancel-unsafe `select!` | Branch futures that lose data when dropped mid-operation (`read_exact` on a split stream, partially consumed bodies) | Restructure into cancel-safe state, or document the invariant |
| Unsafe `Send`/`Sync` | `unsafe impl Send/Sync` outside FFI wrappers, or bounds added only to satisfy the compiler | Prove the guarantee, or change the ownership model |

Report async findings under Design or Complexity with reach, frequency, and the failure scenario (starvation, deadlock, memory growth); a static suspicion alone belongs in Candidates Requiring Measurement.

---

## 6. API and Type Design

| Smell | Detection | Remedy |
|-------|-----------|--------|
| Primitive obsession | `String`/`u64` IDs threaded across modules without newtypes; `&Vec<T>`/`&String` parameters where `&[T]`/`&str` fits (`clippy::ptr_arg`) | Newtypes with validating constructors; borrow the slice |
| Boolean parameter lists | `fn open(path, create, truncate, append, sync)` — call sites unreadable, invalid combinations representable | Enum or options struct |
| Sentinel values | `-1`/`""`/`0` as "absent"; `Option<Option<T>>` for tri-state | Explicit enum |
| Invalid states representable | Public mutable fields, `Default` producing unusable configuration, builder with no `build() -> Result` | Private fields plus checked constructors, typestate |
| Speculative generality | Generic parameter with exactly one instantiation, `Box<dyn Trait>` with one implementor and no planned variation, unused `where` bounds, `#[non_exhaustive]` on a crate-private enum | Delete until a second use exists |
| Conversion soup | Dozens of `impl From<A> for B` across modules, `Into` chains that obscure the authoritative type | One canonical type, conversions at boundaries |
| Leaked abstraction | Public signatures exposing `sqlx::Row`, `hyper::Request`, ORM rows, or private module paths | Own DTOs at the boundary |
| Dispatch mismatch | `dyn` in a hot loop where every type is known statically; generics in public APIs causing monomorphization blow-up | Measure first (`cargo llvm-lines`), then choose |

Rust's closed enums and exhaustive `match` are **not** the "Switch Statements" smell. Report a repeated `match` only when the same variant set is re-matched in several modules and keeps changing (OCP), and prefer trait dispatch only when variation is real.

---

## 7. Testing Health

- **Placement:** `#[cfg(test)] mod tests` covering only private helpers with no `tests/` coverage of the public API; test-only dependencies in `[dependencies]`.
- **Slow or flaky:** real sleeps and clocks (`tokio::time::sleep`) instead of paused time, `#[ignore]`, network/database tests without fixtures, `#[should_panic]` where `Result` is the contract.
- **Coverage by construction:** `--all-features` never run, the feature matrix untested, `#[cfg(target_os = "...")]` branches untested. Report as a coverage limitation, not as a code finding.
- **Verification tooling:** `cargo test --workspace --all-targets`, `cargo test --doc`, `insta` snapshot review, `trybuild` for compile-fail contracts, `cargo +nightly miri test` for `unsafe` (nightly-only; when unavailable record "not measured" rather than assuming soundness).

---

## 8. Complexity and Allocation Hotspots

| Pattern | Detection | Note |
|---------|-----------|------|
| Allocate/format/clone in a loop | `.clone()`, `format!`, `to_string()`, `vec![..]` inside `for`/`map` over large N | Candidate until N and frequency are known |
| Indexed queue on `Vec` | `insert(0, ..)` / `remove(0)` | `VecDeque` |
| Linear membership in a loop | `Vec::contains` / `iter().any()` inside another loop | `HashSet`/`HashMap` |
| Collect then re-iterate | `collect::<Vec<_>>()` followed by another pass | Compose iterators or reuse a buffer |
| Sort inside a loop | Repeated `sort`/`sort_by` | Sort once, or `BinaryHeap` |
| String growth | `push_str`/`+=` without `with_capacity` when the size is known | Reallocation churn |
| Default hasher in a hot path | `HashMap` with `RandomState` queried per request | Measured only; `ahash`/`hashbrown` after measurement |
| Async N+1 | One DB/HTTP call per item inside a loop, no batch endpoint | Batch the calls; `buffer_unordered(n)` only caps concurrency, it does not reduce the number of calls |
| Dynamic dispatch per item | `Box<dyn Trait>` in a hot loop | Generic or enum when measured |

Idiomatic patterns that are **not** findings: iterator chains (`map`/`filter`/`collect`), exhaustive `match`, `Result`-returning functions, explicit `drop`, `?` propagation, and `impl Trait` in argument position.

---

## 9. False-Positive Controls

Read this section before writing any finding; every item here has produced false positives in practice.

- **Generated or derived code:** `OUT_DIR` includes, `include!`, `prost`/`tonic`/`sqlx::query!`/`serde`/`bindgen` output, macro definitions and expansions. Do not report line counts, naming, or duplication there.
- **Not production paths:** `tests/`, `benches/`, `examples/`, `xtask/`, `fuzz/`, `build.rs`, `#[cfg(test)]`. Report them only when they ship or are the sole guard for a critical path.
- **Intentional `unwrap`:** `main`, `Default`/`new` invariants, `OnceCell` initialization, immediately after an explicit `is_some()` check, test helpers, const evaluation.
- **Fail Fast by design:** `assert!`/`debug_assert!` enforcing an internal precondition, and `x[i]`/`&s[a..b]` immediately after a `len()`/`is_some()`/range check. This is the behavior the skill's **Fail Fast** principle asks for; do not report it as a panic on external input.
- **Deliberate encodings:** `Option<Option<T>>` for patch semantics (absent vs explicit null), `#[non_exhaustive]` on a public enum or struct as the API guidelines recommend.
- **Intentional sharing:** `clone()` on `Arc` or on small `Copy` values, `Rc<RefCell>` in single-threaded trees, `Arc<Mutex<..>>` for low-contention caches, `unsafe` in FFI wrappers carrying `// SAFETY:` reasoning.
- **Intentional abstraction:** `Box<dyn Error>`/`anyhow` in binaries and integration tests, `dyn` at plugin boundaries, a long `match` on a closed enum.
- **Macro-heavy crates:** line counts, nesting, and duplication heuristics do not apply to macro definitions.
- **Tool availability:** `cargo geiger`, `cargo llvm-lines`, `cargo udeps`, `miri`, and `cargo llvm-cov` are optional. When a tool is missing, mark that dimension **not measured** in the report instead of implying it is clean.
- **Lint drift:** clippy lint names and groups change between toolchain versions. Discover what the installed toolchain offers with `cargo clippy -- -W help`, and when a lint matters, add it to CI with `-D warnings` so the finding does not depend on a local invocation.

---

## 10. Report Additions

When this profile applies, fill in two places.

**Report header** (the `Language profile` line in [`../SKILL.md`](../SKILL.md)):

- **Language profile:** Rust — crate/target (`lib`/`bin`), edition, and toolchain from `rust-toolchain.toml`.
- **Not measured:** the dimensions skipped and why (missing tool, no runtime access, no workload data).

**Each Rust finding**, on top of the existing template fields:

- **Reachability:** for panic, `unsafe`, and cast findings, the path from input to the site, or an explicit unreachable/undetermined marker.
- **Verification:** make the existing verification field executable — the Cargo command, test name, or benchmark that reproduces the evidence (`cargo clippy ...`, `cargo tree ...`).

Map profile-only signals onto the canonical categories so the report totals stay comparable across languages:

| Rust signal | Canonical category |
|-------------|--------------------|
| Workspace and boundary (§2): logic in binaries, layer leaks, god modules, feature fan-out, visibility, version skew | Architecture / Coupling |
| Ownership/borrowing, interior mutability, globals | Coupling |
| Panics, error handling, casts, `unsafe` | Code (plus Fail Fast when it reflects policy) |
| Async and concurrency | Design / Complexity |
| API and type design | Design / Cohesion |
| Allocation and hot-loop costs | Complexity (Measure First) |
| Testing health | Testing |
