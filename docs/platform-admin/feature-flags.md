# Feature Flags

Feature flags live in `platform.feature_flag_registry`. Tenant overrides live in
`platform.feature_flag_tenant_overrides`.

Feature flags are separate from plan entitlements:

- Plan entitlements define product/package access.
- Feature flags govern rollout, kill switches, and tenant-specific overrides.

Rollout percentages are constrained to `0..100`. Kill switches are returned in
effective entitlement output and should be treated by consumers as overriding
normal enablement.
