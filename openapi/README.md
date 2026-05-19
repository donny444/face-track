# FaceTrack OpenAPI 3.1 specification

Hand-authored, modular OpenAPI 3.1 document for the FastAPI server in
[`server/main.py`](../server/main.py).

FastAPI emits its own runtime spec at
[`/openapi.json`](http://localhost:8000/openapi.json), but that document
is driven entirely off Python type hints — it has no descriptions, no
realistic error examples, no `operationId`s, and no curated tags. This
spec is the editorial counterpart: it is what we publish externally and
diff against the runtime spec when reviewing API changes.

## File layout

```
openapi/
├── openapi.yaml                  # canonical entrypoint (single source of truth)
├── README.md                     # this file
├── paths/                        # one PathItem per file, $ref'd from openapi.yaml
│   ├── attendances.yaml          # GET, POST /attendances/
│   ├── students.yaml             # GET, POST /students/
│   ├── students_by_id.yaml       # DELETE /students/{studentId}
│   ├── instructors.yaml          # POST /instructors/   (login)
│   ├── insights.yaml             # GET  /insights/
│   └── faces.yaml                # GET  /faces/{filename}  (static mount)
└── components/
    ├── schemas/                  # request/response models
    │   ├── AttendanceCreate.yaml
    │   ├── Attendance.yaml
    │   ├── Attendee.yaml
    │   ├── Instructor.yaml
    │   ├── InstructorPublic.yaml
    │   ├── StudentRegistration.yaml
    │   ├── MessageResponse.yaml
    │   ├── AttendanceCreatedResponse.yaml
    │   ├── AttendancesListResponse.yaml
    │   ├── StudentsListResponse.yaml
    │   ├── LoginResponse.yaml
    │   ├── InsightsResponse.yaml
    │   ├── ErrorResponse.yaml
    │   ├── ValidationError.yaml
    │   └── HTTPValidationError.yaml
    ├── responses/                # reusable response envelopes
    │   ├── BadRequest.yaml
    │   ├── Unauthorized.yaml
    │   ├── NotFound.yaml
    │   ├── InternalError.yaml
    │   └── Validation.yaml
    ├── parameters/               # reusable query/path parameters
    │   ├── RecentAttendances.yaml
    │   ├── StudentsHead.yaml
    │   ├── StudentsSearch.yaml
    │   ├── StudentIdPath.yaml
    │   └── FaceFilenamePath.yaml
    └── securitySchemes/
        └── bearerAuth.yaml       # JWT bearer (HS256) — see POST /instructors/
```

Everything is reachable from `openapi.yaml` via `$ref`. Tooling such as
`@redocly/cli` and `@apidevtools/swagger-cli` follow these refs
automatically when you point them at `openapi.yaml`.

## Conventions

- **OpenAPI 3.1** throughout. Nullability is expressed with
  `type: [string, "null"]` (the OAS 3.1 idiom) rather than the legacy
  `nullable: true` boolean.
- **Closed schemas**: every object response uses
  `additionalProperties: false` so consumers can safely deserialise into
  strongly-typed structs.
- **One PathItem per file** under `paths/`. The URL `/students/`
  (collection) and `/students/{studentId}` (item) intentionally live in
  separate files (`students.yaml` and `students_by_id.yaml`).
- **Security by default**: the document declares
  `security: [- bearerAuth: []]` at the root, so every operation
  inherits the bearer requirement. Exempt operations override it with
  `security: []`. This mirrors `auth_middleware.EXEMPT_ROUTES`
  exactly — keep both in sync when adding endpoints.
- **Reusable responses**: 400/401/404/422/500 envelopes are defined
  once under `components/responses/` and `$ref`'d from every operation
  that can produce them.

## Lint / validate

The canonical validator is [Redocly CLI][redocly]. It speaks OAS 3.1
natively and follows external `$ref`s.

```bash
npx --yes @redocly/cli@latest lint openapi/openapi.yaml
```

A clean run prints `Woohoo! Your API description is valid.` and exits 0.

If Redocly is unavailable (offline laptop, corporate proxy, etc.) you
can fall back to swagger-cli, which uses `@apidevtools/swagger-parser`
under the hood and also supports OAS 3.1 as of `v4.0.4`:

```bash
npx --yes @apidevtools/swagger-cli@latest validate openapi/openapi.yaml
```

As a last-ditch sanity check (YAML well-formedness only — does **not**
validate against the OpenAPI schema):

```bash
python -c "import yaml; yaml.safe_load(open('openapi/openapi.yaml'))"
```

## Preview

Redocly ships a one-shot Redoc preview server:

```bash
npx --yes @redocly/cli@latest preview-docs openapi/openapi.yaml
# → open http://127.0.0.1:8080
```

It hot-reloads on save, which is the best workflow for iterating on
prose descriptions.

## Bundle into a single file

For distribution (e.g. uploading to API gateways, generating client
SDKs) it is often convenient to flatten the modular spec into one
self-contained file:

```bash
npx --yes @redocly/cli@latest bundle openapi/openapi.yaml \
  -o openapi/openapi.bundled.yaml
```

The bundled output is not checked into git; regenerate as needed.

## Diffing against the FastAPI runtime spec

FastAPI's auto-generated spec at `/openapi.json` can be compared against
this hand-authored spec to catch drift — e.g. a new endpoint that was
added to `server/main.py` but not yet documented here.

1. Start the server: `uvicorn main:app --reload` from `server/`.
2. Save the runtime spec: `curl http://localhost:8000/openapi.json -o /tmp/runtime.json`.
3. Bundle the hand-authored spec into a single JSON file:
   `npx @redocly/cli bundle openapi/openapi.yaml -o /tmp/hand.json --ext json`.
4. Use [openapi-diff][diff] or `oasdiff` for a semantic compare:

   ```bash
   npx --yes openapi-diff /tmp/hand.json /tmp/runtime.json
   # or
   npx --yes oasdiff diff /tmp/hand.json /tmp/runtime.json
   ```

5. For prose / descriptive drift the FastAPI runtime spec is mostly
   silent, so a manual review is fine — `git diff --no-index` between
   the two files highlights structural deltas.

[redocly]: https://redocly.com/docs/cli/
[diff]: https://github.com/Tufin/oasdiff
