# Round 08 author repair acceptance

Initial independent review is frozen at SHA e8ae5d5f9206c0be618bd2be9dcd3b521b7d8810b97a6bd3d44815fcd4840097. The original author 11 files and the earlier revision_02 remain unchanged. Read revision_02 and this revision_03 together as authoritative amendments.

P1-01 is addressed by the explicit common infinite opaque equality domain and well-typed premise in revision_02 and theory_result.corrected.json. The all-n theorem and canonical-database argument are conditional on that premise. Finite SQL domains are outside this theorem.

P1-02 is addressed by O(S+L+h+v) for the full explicitly encoded input with duplicate-free counted sets. For arbitrary counted-set encodings of total length j, the bound is O(S+L+h+j+v). Only local operations after input reading have O(L+v) cost; the witness-cell bit bound does not include the whole input or output certificate. No isomorphism discovery or hidden chase is included in the same-body construction bound; a different-body application must supply and validate the required transport.

P2-01 is addressed by revision_02: four parallel FKs between a relation pair form one underlying undirected simple-graph adjacency. This is not itself a forest rejection for dev03_06; each full FK and explicit closure still requires checking. Original aggregate syntax independently rejects that original pair. The original 0/21 static applicability denominator remains unchanged, without parser certification or SQL rewriting.

P2-02 is addressed by references.corrected.json: BDFS uses the original PDF linked by Ronald Fagin, Lemma 3.1 plus its following constructive proof, printed pp.33–34 / PDF pp.4–5. DeHaan is the 2009 dissertation; Definitions A.2.1/A.2.2 are printed p.168 / PDF p.188, the multiplicity polynomial discussion p.170 / PDF p.190, and A.2.3–A.2.8 p.171 / PDF p.191. PDF pages here are 1-based. Chirkova–Genesereth v3 anchors name their format: §2.4 HTML Theorem2.3 / PDF Theorem2.2; §6.1 Theorems6.1/6.2 agree; §6.2 HTML Theorem6.5 / PDF Theorem6.3. No unrestricted partial-counting theorem is attributed to their sound bag chase.

This is a scope, cost and citation correction only. Novelty remains NULL; no new mechanism or fair baseline advantage is claimed. Seven base fixtures and three planned interventions remain unexecuted. No original SQL, public-source dataset, frozen experiment or manuscript is changed.
