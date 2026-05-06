---
inclusion: fileMatch
fileMatchPattern: "**/*.java"
---

# Java + Senzing SDK

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess class names or method parameters
- Use try-with-resources or explicit `try/finally` to guarantee engine `destroy()` is called on shutdown and exceptions
- Load engine configuration from a JSON file using `Files.readString(Path)` — never hardcode configuration
- Catch `SzException` (or the SDK-specific exception hierarchy) separately from general exceptions for clear error diagnosis
- Initialize the Senzing engine once at application startup and reuse the instance — do not create/destroy per record
- Use `explain_error_code` via MCP for any Senzing error codes encountered at runtime

## Common Pitfalls

- **Unclosed engine instances**: Forgetting `destroy()` leaks native resources — always use try-with-resources or a shutdown hook (`Runtime.addShutdownHook`)
- **Classpath misconfiguration**: Senzing JARs must be on the classpath — verify with `java -cp` or Maven/Gradle dependency declarations
- **String encoding assumptions**: Always use `StandardCharsets.UTF_8` when converting between `String` and `byte[]` for record payloads
- **Swallowing exceptions**: Never catch and ignore `SzException` — log the error code and message, then use `explain_error_code` for diagnosis
- **Thread-unsafe engine sharing**: The Senzing engine is thread-safe for concurrent calls, but configuration and initialization are not — init once, then share

## Performance Considerations

- Use `ExecutorService` with a fixed thread pool for parallel record loading — Senzing engine handles concurrent `addRecord` calls
- Size the thread pool to match available CPU cores (start with `Runtime.getRuntime().availableProcessors()`)
- Process records in batches of 100-1000 — read a batch, submit to the pool, then read the next
- Tune JVM heap with `-Xmx` (e.g., `-Xmx4g`) for large datasets — Senzing native memory is separate from JVM heap
- Use `BufferedReader` for line-by-line JSONL processing — avoids loading entire files into memory
- Profile with `jvisualvm` or `async-profiler` to identify bottlenecks before optimizing

## Code Style for Generated Code

- Use Maven or Gradle project structure: `src/main/java/` for source, `src/main/resources/` for configs
- One public class per file — match filename to class name
- Use `java.util.logging` or SLF4J for logging — never `System.out.println` in production code
- Store Senzing configuration in `src/main/resources/` or a `config/` directory — load via classpath or file path
- Define a custom exception class wrapping `SzException` if the project needs application-specific error context

## Platform Notes

- Senzing native libraries require `LD_LIBRARY_PATH` (Linux), `DYLD_LIBRARY_PATH` (macOS), or `PATH` additions (Windows) — follow `sdk_guide` output exactly
- JVM version: use Java 11+ — verify with `java -version` before running
- On Linux, ensure the Senzing SDK shared libraries (`.so` files) are accessible — set paths in shell profile or launch script
- On macOS, set `DYLD_LIBRARY_PATH` to include the Senzing `lib` directory — follow `sdk_guide` output
- On Windows, Senzing DLLs must be on `PATH` — the installer typically handles this, but verify if running from IDE. If missing, add the Senzing `lib` directory to `PATH` in your environment script or system settings

## Common Environment Issues

### JAVA_HOME Not Set

**Symptom**: Build tools report "JAVA_HOME is not set" or "Cannot find JDK installation"
**Cause**: The `JAVA_HOME` environment variable is missing or points to a JRE instead of a JDK
**Fix**:

1. Locate your JDK installation: `which java` then follow symlinks, or check `/usr/lib/jvm/` (Linux), `/Library/Java/JavaVirtualMachines/` (macOS), or `C:\Program Files\Java\` (Windows)
2. Set the variable: `export JAVA_HOME=/path/to/jdk-17` (add to `~/.bashrc` or `~/.zshrc`)
3. On Windows: set via System Properties → Environment Variables
4. Verify with: `echo $JAVA_HOME && java -version`

### Classpath Configuration for Senzing JAR

**Symptom**: `ClassNotFoundException` or `NoClassDefFoundError` for Senzing classes at runtime
**Cause**: The Senzing SDK JAR file is not on the Java classpath
**Fix**:

1. Locate the Senzing JAR: typically in `/opt/senzing/lib/` (Linux) or the Senzing installation `lib` directory
2. For direct compilation: `javac -cp /opt/senzing/lib/sz-sdk.jar:. MyApp.java`
3. For Maven/Gradle: add the dependency to your build file (see dependency resolution entry below)
4. Verify with: `java -cp /opt/senzing/lib/sz-sdk.jar:. -verbose:class MyApp 2>&1 | grep -i senzing`

### Maven/Gradle Dependency Resolution Failures

**Symptom**: `Could not resolve dependencies` or `Could not find artifact com.senzing:sz-sdk` during build
**Cause**: The Senzing SDK artifact is not in Maven Central or the repository URL is misconfigured
**Fix**:

1. Check that the Senzing Maven repository is declared in `pom.xml` or `build.gradle`
2. For Maven: add `<repository>` entry pointing to the Senzing repository URL from `sdk_guide` output
3. For Gradle: add `maven { url '...' }` in the `repositories` block
4. Verify with: `mvn dependency:resolve` or `gradle dependencies --configuration runtimeClasspath`

### JDK Version Conflicts

**Symptom**: `UnsupportedClassVersionError`, `invalid source release: 17`, or preview feature errors
**Cause**: The project requires JDK 17+ but the system default is an older version
**Fix**:

1. Check current version: `java -version` and `javac -version`
2. Install JDK 17+: use SDKMAN (`sdk install java 17.0.x-tem`), package manager, or download from Adoptium
3. Set as default: `sdk use java 17.0.x-tem` or update `JAVA_HOME` and `PATH`
4. Verify with: `java -version` — should show 17 or higher

### Module System Access Errors

**Symptom**: `InaccessibleObjectException` or `module java.base does not "opens" ... to unnamed module` at runtime
**Cause**: Java 9+ module system restricts reflective access to internal APIs that Senzing native bindings may require
**Fix**:

1. Add JVM flags to open required modules: `--add-opens java.base/java.lang=ALL-UNNAMED`
2. In Maven: configure `<argLine>` in `maven-surefire-plugin` or `MAVEN_OPTS`
3. In Gradle: add `jvmArgs` to the `run` or `test` task configuration
4. Verify with: `java --add-opens java.base/java.lang=ALL-UNNAMED -jar myapp.jar`
