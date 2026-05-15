---
inclusion: fileMatch
fileMatchPattern: "**/*.{ts,tsx,js,jsx}"
---

# TypeScript + Senzing SDK

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess function names or parameters
- Use `async/await` for all Senzing SDK calls — never use raw callbacks or unhandled promises
- Wrap engine lifecycle in a class with explicit initialization and cleanup methods (call `get_sdk_reference` for current method names) — call cleanup in a `finally` block or process exit handler
- Load engine configuration from JSON files using `fs.readFileSync(path, 'utf-8')` — never hardcode configuration strings
- Define TypeScript interfaces for Senzing record structures — enables compile-time validation of record payloads
- Use `explain_error_code` via MCP for any Senzing error codes encountered at runtime

## Common Pitfalls

- **Unhandled promise rejections**: Always `await` SDK calls or attach `.catch()` — unhandled rejections crash Node.js by default
- **Using `any` for Senzing data**: Define typed interfaces for records, entities, and API responses — `any` defeats TypeScript's safety
- **Blocking the event loop**: Senzing SDK calls may be CPU-intensive — use `worker_threads` for loading operations to keep the main thread responsive
- **Memory leaks from unclosed engines**: Register `process.on('exit', ...)` and `process.on('SIGINT', ...)` handlers to ensure engine cleanup (call `get_sdk_reference` for the current cleanup method name)
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
- On macOS, set `DYLD_LIBRARY_PATH` to include the Senzing `lib` directory — native addons require this for dynamic library resolution at runtime
- On Windows, ensure Senzing DLLs are on `PATH` — native addon loading depends on OS library search paths
- Verify TypeScript/Node.js SDK support status via MCP before generating code — relay any platform warnings to the bootcamper

## Common Environment Issues

### Node.js Version Conflicts

**Symptom**: `SyntaxError: Unexpected token` on modern syntax, or `ERR_UNSUPPORTED_ESM_URL_SCHEME` errors
**Cause**: The installed Node.js version is older than 18, which is the minimum required for Senzing bootcamp exercises
**Fix**:

1. Check current version: `node --version`
2. Install Node.js 18+ via nvm: `nvm install 18 && nvm use 18` (or download from nodejs.org)
3. If using system Node.js: update via package manager (`brew upgrade node`, `sudo apt install nodejs`)
4. Verify with: `node --version` — should show v18 or higher

### Native Addon Build Failures (node-gyp)

**Symptom**: `gyp ERR! build error` or `Cannot find module '../build/Release/senzing.node'` during install
**Cause**: node-gyp requires Python 3 and a C++ compiler to build native addons, and these are missing or misconfigured
**Fix**:

1. Install build prerequisites: `npm install -g node-gyp` and ensure Python 3 is available
2. On Linux: `sudo apt install build-essential python3`
3. On macOS: `xcode-select --install`
4. On Windows: `npm install -g windows-build-tools` or install Visual Studio Build Tools
5. Verify with: `node-gyp configure` — should complete without errors

### ESM vs CommonJS Module Resolution

**Symptom**: `ERR_REQUIRE_ESM` when importing Senzing, or `SyntaxError: Cannot use import statement outside a module`
**Cause**: Mismatch between the project's module system (ESM vs CJS) and how the Senzing package exports its bindings
**Fix**:

1. For ESM projects: ensure `"type": "module"` is in `package.json` and use `import` syntax
2. For CJS projects: use `require()` or dynamic `import()` for ESM-only packages
3. In `tsconfig.json`: set `"module": "ESNext"` and `"moduleResolution": "bundler"` (or `"node16"`)
4. Verify with: `npx ts-node --esm src/index.ts` or `node --loader ts-node/esm src/index.ts`

### TypeScript Strict Mode Type Errors

**Symptom**: `TS2322: Type 'X | undefined' is not assignable to type 'X'` or `TS7053: Element implicitly has an 'any' type`
**Cause**: TypeScript strict mode (`strict: true` in tsconfig) catches nullable and untyped values that Senzing API responses may return
**Fix**:

1. Use optional chaining and nullish coalescing: `const value = response?.nestedField?.property ?? "default"` (call `get_sdk_reference` for current response structure fields)
2. Add type guards before accessing properties: `if (result !== undefined) { ... }`
3. Create typed interfaces for Senzing responses and use type assertions where the API contract is known (call `get_sdk_reference` for current response schemas)
4. Verify with: `npx tsc --noEmit` — should compile without type errors

### Package Manager Conflicts

**Symptom**: `ERESOLVE unable to resolve dependency tree` or lockfile conflicts between npm, yarn, and pnpm
**Cause**: Multiple package managers have been used in the same project, creating conflicting lockfiles and node_modules structures
**Fix**:

1. Choose one package manager and remove others' lockfiles: keep only `package-lock.json` (npm), `yarn.lock` (yarn), or `pnpm-lock.yaml` (pnpm)
2. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install` (or equivalent)
3. Add other lockfiles to `.gitignore` to prevent accidental commits
4. Verify with: `npm ls` (or `yarn list`, `pnpm list`) — should show clean dependency tree without errors

## SDK Maturity Notes

> **Note:** TypeScript/Node.js SDK support may have fewer `find_examples` results
> compared to Python and Java. The MCP server's `generate_scaffold` and `sdk_guide`
> tools produce equivalent-quality output for all supported workflows. If you
> encounter a gap, use `search_docs` or ask for help.
