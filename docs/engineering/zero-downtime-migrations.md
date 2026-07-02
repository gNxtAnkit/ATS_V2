# Zero-Downtime Migration Rules

Future migrations must follow expand/migrate/contract:

1. Add nullable structures and backwards-compatible code.
2. Backfill in bounded batches.
3. Switch reads and writes safely.
4. Add constraints only after data is valid.
5. Remove old structures in a later release.

Avoid destructive operations in the same deployment that introduces replacement behavior.
