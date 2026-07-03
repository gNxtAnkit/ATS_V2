# Plan, Quota, Feature, and Add-On Management

Platform Admin Service manages the platform catalogue:

- Plans
- Quota definitions
- Feature definitions
- Plan feature entitlements
- Plan quota limits
- Add-ons
- Add-on quota deltas
- Add-on feature entitlements

Plans and add-ons use the actual schema status values:

- `draft`
- `active`
- `deprecated`
- `archived`

The API uses `archived` for retire operations because the schema has no
`retired` enum value.

Plan and add-on entitlement replacement endpoints validate referenced feature
and quota definitions before writing rows. Mutations write platform audit logs.
