# Round 06 theory scope correction, revision 02

This is the authoritative scope correction to the preserved initial `literature/EQUITABLE_QUOTIENT_FALSIFICATION.zh.md`. It responds to independent review; the original 115-file snapshot remains unchanged. No SQL, SMT, or scientific experiment was rerun. The decision remains **REJECT; retained hypothesis = null**.

## P_lift requires disjoint primary-key and foreign-key source fields

Replace the original S0 field-overlap conditions with the following narrower conditions:

- Each table has one non-NULL primary-key column in its own opaque key domain.
- Each foreign key is a non-NULL total function to the complete referenced primary key.
- Foreign-key source columns are pairwise disjoint and are disjoint from their source table's primary-key column.
- Payload means precisely the remaining columns, disjoint from all PK and FK source columns. Payload is non-NULL; any admitted row predicates apply only to payload.
- All remaining restrictions of the initial S0 still apply, including sufficient fresh-key capacity and no cross-FK coupling or additional uniqueness constraints.

Under these conditions the existing construction can first allocate distinct PKs and then fill each independent FK source column without overwriting a PK or payload. The count-preserving query fragment remains the initial alias-simple-tree-single-edge fragment. This is a scope repair, not a new lifting algorithm or a broader theorem.

**Independent review's counterexample to the original broad P_lift:** let `T(id PK, payload)` also declare the same `id` column as a self-FK to `T.id`. Propose two quotient classes with distinct payloads, each of size 1, pointing to each other, each with degree 1. All initial size/degree balance equations hold. Yet a physical row's `id` can reference only the same unique `id` row, hence itself; it cannot point to the distinct-payload class. The certificate is unrealizable. This is a manual counterexample, not a database execution. It shows why source-FK/PK overlap cannot remain implicitly allowed in P_lift.

The correction does not claim that every overlapping-key schema is impossible. Such schemas would need extra joint realizability conditions, absent here. The original broader P_lift is withdrawn.

## Distinguish the historical selector from the formal query fragment

The frozen `data/` selector uses stronger schema-forest and one-alias-per-table filters. The formal theory permits repeated table names when the query alias graph remains a simple tree with one FK condition per edge and no alias disequalities. These are different conditions; repeated base-table use alone is not a valid rejection reason for that formal fragment.

The original-pair applicability count nevertheless remains **0/21** under an independently sufficient necessary condition: none of those 21 original pairs has both queries in the required pure `COUNT(*)` tree-join form. Ratios, DISTINCT, outer joins, anti-existence, other aggregates, and unrelated projections must not be deleted or rewritten to manufacture applicability. This is a static scope classification, not parser or SQL execution evidence. The earlier selector files are preserved as historical records; this correction supersedes their overly strong identification of schema/table restrictions with the formal alias fragment.

No part of this correction changes the registered 12-slot generation/replay experiment, its timing, its complete failure denominator, or its results. The existing quotient/indexing precedents continue to defeat the novelty claim. The research as a whole remains ongoing.
