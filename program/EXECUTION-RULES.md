# Transformation execution rules

1. Work multiple independent lanes in parallel, but never create overlapping writers to the same production surface.
2. Prefer reversible branches/PRs and preview environments. Main, DNS, archives and runtime identities are late-stage changes.
3. A repository move never changes semantic profile identity.
4. A product rename never silently changes bundle IDs, Keychain services, stores, file encodings, URLs, CLI contracts or signing identity.
5. Preserve source commit provenance when importing a definition. Large profile+tool hybrids are split, not flattened.
6. Public Hub/MCP receive definitions and public metadata, not private Prim instances.
7. Build/test/review/release/deploy/real-use are separate states.
8. Stop only at a genuine gate requiring founder intent, credentials, legal/governance review, spend approval, or a real device/account. Record the gate and keep other lanes moving.
9. No background/unattended work is implied by this repository. CI is bounded verification.
10. Archive only after successor + compatibility + rollback + real-use proof. Never delete history as cleanup.
