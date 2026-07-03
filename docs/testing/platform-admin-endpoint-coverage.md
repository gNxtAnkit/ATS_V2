# Platform Admin Endpoint Coverage

Run:

```bash
make smoke-platform-admin-api
```

Generated report:

```text
artifacts/platform-admin-api-coverage.md
```

The generated report includes method, endpoint, execution status, auth coverage, permission coverage, audit coverage, and notes. Do not mark an endpoint complete manually; rerun the smoke script after backend route changes.

Current known limitation: this repository change adds the coverage generator, but this environment did not have running local Identity and Platform Admin services, so the generated artifact was not produced during implementation.
