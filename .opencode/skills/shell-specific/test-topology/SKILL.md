---
name: test-topology
description: "Use when placing, creating, or refactoring SHELL tests by ownership and architectural scope."
---

# SHELL Test Topology

Tests follow production ownership and must not widen a package boundary accidentally.

- `shell/tests/platform/` tests only `shell.platform`; it has zero BC imports.
- `shell/tests/<bc>/` tests one BC and may import only that BC plus `shell.platform`.
- `shell/tests/contracts/` tests public HTTP/event contracts between BCs using payloads, schemas, ASGI apps, or transport doubles rather than private repositories.
- `shell/tests/system/` tests scenarios involving several separately started BC applications. It must not create a shared container or shared database.
- `shell/tests/architecture/` contains repository-wide AST, import, naming, topology, and dependency checks. It is not a platform test.
- `shell/tests/shared/` contains only generic helpers and doubles with no BC imports.

When a test in `platform` imports a BC, either replace the BC sample with a platform fake/contract fixture or move the test to `shell/tests/<bc>`. When a test checks repository-wide rules, keep it in `architecture` even if the rule concerns platform.
