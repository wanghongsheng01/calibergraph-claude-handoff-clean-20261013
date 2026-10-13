# Cohen 2009 / PODS 2006: bounded primary-source follow-up

Date: 2026-10-11. Scope: public primary-source retrieval and reading only. No scientific code was run; no theory or independent-review file was read or changed. The current two-corner proof was not reviewed in this task.

**Outcome: UNRESOLVED.** No readable full text of Cohen 2009 or PODS 2006 was obtained. The specific two-corner prior-art question remains open; this search supplies no basis for declaring novelty or absence of a prior result.

The question is whether the original proof already yields: for a common finite relational core body B, fixed head, full-tuple keys and no foreign keys, equality of the two counting queries on just D_M and D_N (clone each element of the indicated count set twice and every other element once) forces equivalence.

## Bibliographic correction verified from the publisher

The DOI [10.1007/s00778-008-0122-1](https://link.springer.com/article/10.1007/s00778-008-0122-1) is **Equivalence of queries that are sensitive to multiplicities**, The VLDB Journal 18, 765–785 (2009), published 15 January 2009. *Equivalence of queries combining set and bag-set semantics* is the PODS 2006 title, DOI [10.1145/1142351.1142362](https://doi.org/10.1145/1142351.1142362), pp. 70–79. The Springer page's Additional information identifies reference 7 as the earlier version and says the extension adds bag semantics. This metadata was directly read, not inferred from a later citation.

## Retrieval evidence

| Source | What was actually available/read | Limit |
|---|---|---|
| [Springer publisher page](https://link.springer.com/article/10.1007/s00778-008-0122-1) | Abstract, references, metadata, Additional information; page explicitly labels itself subscription preview | No Section 5 text, Lemma 5.2, Theorem 5.3, or original proof obtained. No login, purchase, or access-control workaround attempted. |
| [Author's university publications page](https://www.cs.huji.ac.il/~sara/publications.html) | Retrieval helper directly read both 2009 and 2006 entries; their links point to the above DOIs | No author-PDF link was present for either target entry. |
| [Author's university research page](https://www.cs.huji.ac.il/~sara/research.html) | Retrieval helper directly read the query-equivalence section listing PODS 2006 | DOI link only for the target. |
| [Author homepage](https://www.cs.huji.ac.il/~sara/) | Retrieval helper read the public homepage | Does not establish access to the old proof. |
| [Official PODS 2006 program](https://sigmod.org/publications/pastconf/sigmod2006/PODS-program.htm) | Target presentation and Sara Cohen/Technion attribution visible | Conference-program metadata, not the paper. |
| [Official VLDB repository entry](https://vldb.org/vldb_journal/index.php/component/remository/Published-Articles/Volume-18/Number-3/Equivalence-of-queries-that-are-sensitive-to-multiplicities-/) | Directly opened; target title, navigation, repository shell only | No readable paper or exposed download link returned. |
| [Sogang university candidate PDF](https://dblab.sogang.ac.kr/sigmod2006/pods/p70.pdf) | Helper discovered this URL as the iframe target of [Sciweavers' record](https://www.sciweavers.org/read/equivalence-of-queries-combining-set-and-bag-set-semantics-50850) | Open and bounded recheck timed out. Full text, authenticity, and content remain unverified; the discovery page is not used as substantive evidence. |

The earlier ACM PDF failure was supplied by the parent; this follow-up did not claim to have read it. Search-result snippets and third-party summaries were not treated as original proof text.

## Primary text actually read: Few Rows v1, not the 2009 proof

Source: Sara Cohen, [Few Rows Tell Them Apart, arXiv:2609.09978v1](https://arxiv.org/html/2609.09978v1), dated 9 September 2026. Directly read Section 3, Appendix A (Definition A.1 and Proposition A.3 with its proof sketch), and Appendix B.1 (proofs of Proposition 5 and Theorem 7).

- Appendix A.3 explicitly attributes its multiplicity-polynomial degree bound, positive characteristic monomial, and homomorphism criterion to Cohen 2009 Lemma 5.2 / Theorem 5.3.
- Section 3 and Appendix B.1 use the characteristic monomial and the Combinatorial Nullstellensatz to obtain **some** vector a in {1,2}^m. The read proof does not prescribe all coordinates as 2 or identify the two D_M/D_N databases of the common-core claim.
- This verifies what the 2026 text states and cites. It does not establish what the unread 2009 proof contains, nor prove that the two-corner result cannot be an immediate specialization of that proof.

Use the section names above within the [read HTML version](https://arxiv.org/html/2609.09978v1). The tool-rendered text placed A.3 at lines 406–424 and the Theorem 7 proof at lines 439–445; these are retrieval text lines, **not** printed page numbers. The original 2009 printed page for Lemma 5.2 / Theorem 5.3 remains unverified.

## Decision boundary

Maintain the existing novelty HOLD / NULL. The direct prior-art gap is not closed. Do not describe the two-corner claim as new on the ground that the accessible 2026 proof ranges over a whole Boolean cube. Equally, this bounded retrieval does not establish that Cohen 2009 already proves the two-corner result. A lawful readable copy of the original Section 5/proof, or a readable PODS 2006 author manuscript with the corresponding argument, is the missing evidence.

Parent-supplied governance status: DataHub entry inspection found no matching fixed module; canonical registry modification is outside the allowed scope, so DATAHUB_REGISTRATION_BLOCKED remains. Private backup is delegated to the root task; this subtask does not claim a completed backup. No third-party paper was stored as a durable workspace artifact.
