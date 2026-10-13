# Round 08 scope and cost correction, revision 02

This correction is authoritative when reading the unchanged original 11-file author snapshot. It does not introduce a new mechanism, execute fixtures, or change the NULL novelty decision. The original hand proof is retained only under the explicit conditions below.

## Equality domain and typing

Add to the fragment definition: every variable and column uses one common infinite opaque equality domain; all atoms, repeated variables, keys, FKs, and head positions are well typed over that domain. There are no coercions, collation rules, NULL values, arithmetic operations, or fixed finite-width SQL types. A repeated variable denotes the same value in every occurrence. The fresh tags used for different variables and indices are pairwise distinct domain elements.

This explicit domain assumption supports `T(n)` for every positive integer n and the distinct-variable canonical databases used in the different-body lemma. It is not a theorem for every actual SQL type or finite domain. A finite-domain adaptation would need a separate capacity and typing admission argument, including enough distinct representatives for every required variable/index tag; that adaptation is not supplied here. The hand fixtures use small integers only as names for opaque values, not as a claim of complete integer/SQL dialect coverage.

## Full input cost

Let S be the full encoded schema length, including all tables and columns (also unused tables), PKs, nullability declarations, all FK metadata, and the schema graph. Let L be the number of variable occurrences in the explicit body, h the total encoded ordered-head length including repeated positions, and v the number of distinct body variables. These use the explicit integer-ID representation assumed in the original word-operation model.

Replace every full-pipeline or full-input `O(L+f+v)` / `O(L+v)` claim with **O(S+L+h+v)** word operations. This includes reading and validating the complete schema and head; checking the FK graph and explicit closure; comparing aligned bodies/heads; building FD and incidence lists; closure propagation; and constructing/checking the fixed `T(2)` witness. A local closure propagation or component traversal alone can still use O(L+v) after those inputs have been read and indexed.

The `T(2)` data cells themselves take O(L log(v+1)) bits in the tagged-value representation. That figure is only the database output, not the cost of reading the complete schema or materializing an arbitrarily long repeated head. Full bit cost must also include the encoded input and any head/certificate output. No claim is made that arbitrary black-box SQL evaluation has this linear cost. The already explicit FK-closed body size remains charged; no implicit chase-size reduction is introduced.

## Parallel-FK applicability wording

The frozen theorem explicitly defines its FK restriction using the **underlying undirected simple graph**. Thus the applicability entry for `dev03_06` must not leave the treatment of parallel FK edges unspecified: parallel edges between the same relation pair do not by themselves violate that simple-graph forest condition. Directed cycles, full-key targets, and explicit body closure still need their own checks.

This corrects one constraint-side uncertainty in the static applicability report. The source's original syntax still gives an independent out-of-fragment reason; the fixed 0/21 literal original-pair applicability result remains unchanged. No SQL was rewritten, no additional C was dropped, and no parser or engine was executed.

## Status

The theorem remains an FD/Armstrong/canonical-database specialization, with no claimed novelty or fair baseline advantage. This correction is awaiting independent followup review. The seven base fixtures and three described ablation interventions remain unexecuted; their existence is not empirical evidence. The overall research continues in a separate self-join/counting-query analysis.
