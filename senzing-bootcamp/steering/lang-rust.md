---
inclusion: fileMatch
fileMatchPattern: "**/*.rs"
---

# Rust + Senzing SDK

## Senzing SDK Best Practices

- Always check MCP server (`get_sdk_reference`) for current Rust SDK availability — Rust bindings may be community-maintained or experimental
- Use RAII patterns for engine lifecycle — wrap the engine in a struct that calls the cleanup method in its `Drop` implementation (call `get_sdk_reference` for the current method name)
- Load engine configuration from JSON files using `std::fs::read_to_string` — deserialize with `serde_json`
- Use `Result<T, E>` for all SDK operations — propagate errors with `?` operator rather than `unwrap()`
- Define a custom error enum (using `thiserror`) that wraps Senzing error codes alongside I/O and serialization errors
- Initialize the engine once in `main()` and pass references to worker functions — avoid global mutable state

## Common Pitfalls

- **Calling `unwrap()` on SDK results**: Senzing operations can fail — use `?` or `match` to handle errors gracefully instead of panicking
- **Unsafe FFI without validation**: If using C FFI bindings to Senzing, validate all pointers and return codes — wrap unsafe blocks tightly
- **Lifetime issues with engine references**: The engine must outlive all threads using it — use `Arc<Engine>` for shared ownership across threads
- **Ignoring `serde` encoding**: Use `serde_json::from_str` with explicit UTF-8 handling — Senzing records may contain international characters
- **Large stack allocations**: Senzing JSON responses can be large — use `String` (heap) not fixed-size arrays for response buffers

## Performance Considerations

- Use `rayon` for parallel record processing — `par_iter()` over record batches distributes work across CPU cores automatically
- Use `crossbeam-channel` for producer-consumer patterns — one thread reads files, workers call the engine concurrently
- Process records in batches of 100-1000 — use iterators and `chunks()` for memory-efficient batching
- Rust's zero-cost abstractions mean iterator chains compile to tight loops — prefer `iter().map().filter()` over manual loops
- Use `BufReader` for line-by-line JSONL processing — avoids loading entire files into memory
- Profile with `cargo flamegraph` or `perf` before optimizing — Senzing native calls dominate runtime

## Code Style for Generated Code

- Use standard Cargo project layout: `src/main.rs` for binaries, `src/lib.rs` for libraries, `config/` for JSON configs
- Define a `mod error` with a custom error type — implement `std::fmt::Display` and `std::error::Error`
- Use `clap` for CLI argument parsing — provide `--input`, `--config`, and `--batch-size` flags
- Use `tracing` or `log` + `env_logger` for structured logging — never `println!` in production code
- Organize modules: `mod config`, `mod engine`, `mod loader`, `mod query` — keep `main.rs` thin

## Platform Notes

- Rust SDK bindings may require linking to Senzing C libraries — set `LIBRARY_PATH` and `LD_LIBRARY_PATH` on Linux
- Cross-compilation (e.g., `x86_64-unknown-linux-gnu` from macOS) requires the target Senzing libraries — native builds are simpler
- Verify Rust SDK support status via MCP before generating code — relay any platform warnings to the bootcamper
- Use `cfg` attributes for platform-specific code paths: `#[cfg(target_os = "linux")]` vs `#[cfg(target_os = "windows")]`
- On Windows, ensure Senzing DLLs are discoverable — set `PATH` or use `build.rs` to configure linker search paths

## Common Environment Issues

### Senzing Sys Crate Build Failures

**Symptom**: `error: failed to run custom build command for` the Senzing sys crate with messages about missing `cc`, `pkg-config`, or header files
**Cause**: The sys crate requires a C compiler and pkg-config to link against Senzing native libraries, and these build tools are not installed
**Fix**:

1. On Linux: `sudo apt install build-essential pkg-config` (Debian/Ubuntu) or `sudo dnf install gcc pkg-config` (Fedora)
2. On macOS: `xcode-select --install` (installs Clang and build tools)
3. On Windows: install Visual Studio Build Tools with "Desktop development with C++" workload
4. Verify with: `cc --version && pkg-config --version`

### Linking Errors for Native Libraries

**Symptom**: `error: linking with cc failed` or `ld: cannot find -lSz` during `cargo build`
**Cause**: The linker cannot find Senzing shared libraries because `LD_LIBRARY_PATH` or `LIBRARY_PATH` is not set
**Fix**:

1. Set library search path: `export LIBRARY_PATH=/opt/senzing/lib:$LIBRARY_PATH`
2. Set runtime path: `export LD_LIBRARY_PATH=/opt/senzing/lib:$LD_LIBRARY_PATH`
3. Alternatively, add a `build.rs` with `println!("cargo:rustc-link-search=/opt/senzing/lib")`
4. Verify with: `cargo build 2>&1 | grep -i "linking"` — should complete without errors

### Cargo Feature Flag Configuration

**Symptom**: `unresolved import` or `no method named` errors for Senzing SDK functions that should exist
**Cause**: The Senzing crate requires specific feature flags to enable optional API modules, and they are not activated in `Cargo.toml`
**Fix**:

1. Check available features: `cargo doc --open` or review the crate's `Cargo.toml`
2. Enable required features in your `Cargo.toml` (call `get_sdk_reference` for current crate name and available features)
3. For specific modules only: enable individual feature flags as documented by the crate
4. Verify with: `cargo check` — should compile without unresolved import errors

### MSVC vs GNU Toolchain Issues on Windows

**Symptom**: `link.exe not found` or ABI mismatch errors when building on Windows
**Cause**: Rust defaults to the MSVC toolchain on Windows, but the Senzing libraries may be built with a different ABI, or MSVC build tools are not installed
**Fix**:

1. Check current toolchain: `rustup show`
2. Install MSVC build tools: download Visual Studio Build Tools, select "Desktop development with C++"
3. If Senzing requires GNU ABI: `rustup default stable-x86_64-pc-windows-gnu`
4. Verify with: `cargo build --target x86_64-pc-windows-msvc` (or `-gnu` depending on Senzing build)

### Lifetime and Borrow Checker Patterns for Senzing FFI

**Symptom**: `borrowed value does not live long enough` or `cannot move out of` errors when passing data to/from Senzing engine
**Cause**: Senzing FFI wrappers return data tied to the engine's lifetime, and Rust's borrow checker enforces these constraints strictly
**Fix**:

1. Clone response strings immediately: `let result = engine.call_sdk_method(id)?.to_owned()` (call `get_sdk_reference` for the actual method name)
2. Use `Arc<Engine>` for shared ownership across threads instead of passing references
3. For callbacks, use `'static` bounds and move closures: `move |data| { ... }`
4. Verify with: `cargo check` — should compile without lifetime errors
