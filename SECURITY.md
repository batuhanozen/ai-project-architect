# Security

This is an unauthenticated, single-operator prototype. Do not expose it to untrusted users or store sensitive project descriptions. The development credentials in `.env.example` are placeholders for a local machine.

Compose publishes ports only on loopback. API and frontend containers are configured to use non-root users, read-only root filesystems, a writable temporary directory, dropped capabilities, and no-new-privileges. These settings have been reviewed statically; their runtime behavior has not been verified because Docker is unavailable on the verification host.

The backend accepts only the PostgreSQL psycopg driver, masks credentials in settings representations, and builds connection URLs safely from separate credentials. CORS rejects wildcard and malformed origins. Pool acquisition, connection establishment, and PostgreSQL statement execution have configured limits; these are not a guarantee of a single end-to-end deadline during every network failure. Shutdown disposes the connection pool.

Health responses contain only a status or generic error. Readiness checks required columns without reading stored descriptions. Unexpected API errors return a generic 500 with a request ID. Request logs exclude query strings, unknown raw paths, request bodies, and exception messages. Run Uvicorn with `--no-access-log` as shown in the README to avoid a second log stream containing raw URLs.

The local Compose database account is the PostgreSQL image's bootstrap superuser and also runs migrations. This is a development convenience; a deployed service needs separate migration and restricted runtime roles. Changing `.env` does not rotate credentials in an existing PostgreSQL volume. Authentication, tenant isolation, rate limiting, TLS, dependency vulnerability scanning, and production secret distribution remain outside this verification. Backend dependency ranges and image tags are not a reproducible release lock.

Future AI inputs and outputs must be treated as untrusted. Validate lengths and schemas, display generated text as text, and never execute generated SQL, code, commands, or scripts. Provider API keys belong on the backend only. Do not log secrets or raw prompts.

Please report vulnerabilities privately to the repository owner through GitHub's private vulnerability reporting feature, if enabled, or by contacting the maintainer directly. Avoid putting exploit details in public issues.
