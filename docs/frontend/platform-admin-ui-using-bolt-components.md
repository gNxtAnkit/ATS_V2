# Platform Admin UI Using Bolt Components

The copied Bolt source is located at:

```text
bolt UI files for identity/project
```

Inspected reusable Bolt patterns:

- auth shell and brand panel
- app shell
- sidebar and topbar
- mobile bottom tabs
- buttons, alerts, inputs, OTP input, password strength, QR code
- auth session/storage/guards
- platform-admin login and MFA pages

The current Platform Admin app keeps the existing generated auth flow and extends it with the same compact admin-shell visual language: sidebar, topbar, panels, metric cards, notices, dense tables, and JSON detail drawers for audit/control-plane payloads.

Future refinement should physically split the current single-file UI into the reusable Bolt component folders (`components/layout`, `components/ui`, `features`, `lib`) once the API surface stabilizes.
