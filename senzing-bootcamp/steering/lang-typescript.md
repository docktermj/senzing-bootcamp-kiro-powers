---
inclusion: fileMatch
fileMatchPattern: "**/*.{ts,tsx,js,jsx}"
---

# TypeScript + Senzing SDK

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess function names or parameters
- Use `async/await` for all Senzing SDK calls — never use raw callbacks or unhandled promises
- Wrap engine lifecycle in a class with explicit `init()` and `destroy()` methods — call `destroy()` in a `finally` block or process exit handler
- Load engine configuration from JSON files using `fs.readFileSync(path, 'utf-8')` — never hardcode configuration strings
- Define TypeScript interfaces for Senzing record structures — enables compile-time validation of record payloads
- Use `explain_error_code` via MCP for any Senzing error codes encountered at runtime

## Common Pitfalls

- **Unhandled promise rejections**: Always `await` SDK calls or attach `.catch()` — unhandled rejections crash Node.js by default
- **Using `any` for Senzing data**: Define typed interfaces for records, entities, and API responses — `any` defeats TypeScript's safety
- **Blocking the event loop**: Senzing SDK calls may be CPU-intensive — use `worker_threads` for loading operations to keep the main thread responsive
- **Memory leaks from unclosed engines**: Register `process.on('exit', ...)` and `process.on('SIGINT', ...)` handlers to ensure engine cleanup
- **Implicit encoding issues**: Always pass `'utf-8'` to `fs.readFileSync` and `Buffer.toString()` — Node.js defaults can vary

## Performance Considerations

- Use `worker_threads` for parallel record loading — each worker gets its own engine instance, bypassing the single-threaded event loop
- Use Node.js `readline` or streaming APIs for JSONL processing — avoids loading entire files into memory
- Process records in batches of 100-1000 — use async generators (`async function*`) for memory-efficient streaming
- Implement backpressure with `stream.Writable` or manual flow control — prevents memory buildup when loading faster than the engine processes
- Profile with `node --prof` or `clinic.js` before optimizing — identify whether bottleneck is I/O, CPU, or memory
- For large datasets, prefer `fs.createReadStream` over `fs.readFileSync` — streaming reduces peak memory usage

## Code Style for Generated Code

- Project layout: `src/` for TypeScript source, `config/` for JSON configs, `data/` for input/output, `dist/` for compiled output
- Use `interface` (not `type`) for Senzing record and entity shapes — interfaces are extendable and produce clearer error messages
- Use a custom error class extending `Error` for Senzing-specific errors — include the error code as a property
- Use `winston` or `pino` for structured logging — never `console.log` in production code
- Use `commander` or `yargs` for CLI argument parsing — provide `--input`, `--config`, and `--batch-size` flags
- Enable `strict: true` in `tsconfig.json` — catches null/undefined issues in Senzing API responses

## Platform Notes

- TypeScript SDK bindings for Senzing may use Node.js native addons (N-API) — ensure `node-gyp` build tools are installed
- Use ESM (`"type": "module"` in `package.json`) for new projects — CJS is legacy but may be required by some Senzing bindings
- On Linux, set `LD_LIBRARY_PATH` for Senzing shared libraries before running `node` or `ts-node`
- On Windows, ensure Senzing DLLs are on `PATH` — native addon loading depends on OS library search paths
- Verify TypeScript/Node.js SDK support status via MCP before generating code — relay any platform warnings to the bootcamper
