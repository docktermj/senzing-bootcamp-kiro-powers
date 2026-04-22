---
inclusion: fileMatch
fileMatchPattern: "**/*.rs"
---

# Rust + Senzing SDK

## Senzing SDK Best Practices

- Always check MCP server (`get_sdk_reference`) for current Rust SDK availability — Rust bindings may be community-maintained or experimental
- Use RAII patterns for engine lifecycle — wrap the engine in a struct that calls `destroy()` in its `Drop` implementation
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
