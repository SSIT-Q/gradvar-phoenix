# Correction log: literature map, version 1 to version 2

- **Document.** `lit_breakthrough_map_2026-09-22.md`. The independent reviewer read version 1; version 2 carries the fixes.
- **Reviewer.** An independent reviewer sub-agent that did not write the map, working on 23–24 September 2026.
  - **Sources checked against.** Pre-registrations v0.15.1 and v0.6.0 on `main`: Section 3c is identical at 369af38 and at 796587a. Also the six track reports, Crossref and the arXiv API.
  - **Review record.** [review_lit_breakthrough_map_2026-09-22.md]({{artifact:f14b12da-f6a9-43e9-9d0c-48c3dc811245}})
- **Verdict.** GO_WITH_CORRECTIONS: 2 must-fix, 12 should-fix and 7 optional corrections, all applied in version 2.

| # | Severity | Correction | Addressed in version 2 |
|---|---|---|---|
| 1 | must fix | The non-resolving Angrisani DOI is not in Section 3c. Section 3c cites arXiv 2409.01706, which resolves. The bad DOI sits in the decision memo's ONOS row and the programme literature list | Bottom line, item 6 and §2.1 now separate the Section 3c mis-attribution from the DOI error in the decision memo and literature list; §8 adds the corrected ONOS row |
| 2 | must fix | "l = 4 first" departs from the pre-registered restoration order | Item 2 restores k = 1 at L = 12, then l = 4, then k = 1 at L = 8 with its control, in the surplus rule's second tier. The header states the pre-flight review and that Owais arms and dispatches |
| 3 | should fix | Three H7 passages use the c^(l/2) form; the simulated RMS differs in slope, not by a constant of order one | Item 1 now covers the hypothesis, the resolvability sentence and the Analysis fit, and proposes an analysis-only clarification. §3.2 gives the reviewer's ratios (1.2 to 1.6 at l = 2; 0.43 to 0.61 at l = 4) |
| 4 | should fix | Kappa cannot explain the n = 19 flag or the 2.3x rung | §4.1 presents kappa as the leading candidate for the n = 85 flag only, with draw-sampling fluctuation as the null, and cites the Deviation 19 record (0.84x, 0.70x, 2.3x; the n = 19 flag is not monotone) |
| 5 | should fix | Draw-level bootstrap and kurtosis reporting are already pre-registered; the z = -3.2 illustration does not describe the recorded flag | §4.2 and item 4 state the pre-registered statistics (10,000 resamples; about 5 sigma by bootstrap at n = 85; z about -4.0 at n = 19). The illustration is removed. The new elements are listed, with the heavy-tail caveat |
| 6 | should fix | Paper 2 Q1 already uses a differential estimator, H1 already takes 2e-5 as its prediction, and Q2 already tests beyond T1. Deviation 9 is unsigned | Item 8 and §6 are rewritten around the open points. Protocol changes go through their own Deviation, or the whole Deviation 9 package is re-reviewed |
| 7 | should fix | The Paper 2 Nature-family estimate was misquoted | §7 restores 1 to 2 % per direction (earlier estimate, not re-assessed) |
| 8 | should fix | "Outside the no-Paper-3 rule" could be read as "exempt from it" | §7 now reads "excluded by the no-Paper-3 rule (Owais, 21 Sep); listed for completeness, not recommended" |
| 9 | should fix | Lerch et al. Theorem 1 is the quantum-enhanced surrogate; the classical small-angle result is Theorem 2 | Bottom line, item 6 and §2.1 distinguish the two theorems; Section 3c needs Theorem 2 |
| 10 | should fix | Shirgure et al. Lemma 3 and Schuster et al. Corollary 2 were over-read | Bottom line and §5 gloss Lemma 3 accurately and call the H6 link an analogy. Corollary 2 is cited as simulability context, "on most input states" |
| 11 | should fix | The item 3 proposal conflicted with Deviation 40, and "H5 variance ratio" was ambiguous | Item 3 names the p = 0.5 over p = 0.25 ratio. The k = 1 rows stay upper bounds and form no ratio |
| 12 | should fix | Rastering adds circuits and job constants | Item 5 costs the nulls, anchors and job constants (3.0 s per job; Deviations 48 and 55) at re-package. The header states the pre-flight review |
| 13 | should fix | The existing ONOS request uses the bad DOI, and the CSV did not match the ONOS table | §8 adds the Angrisani PRL Supplemental Material row at 10.1103/lh6x-7rc3, noting that arXiv v2 probably suffices. The CSV gains an onos_priority column that matches §8 |
| 14 | should fix | Schuster and Yao's result was stated as fact | §3.1 now reads "conjecture" |
| 15 | optional | Proven-edge arithmetic, and the sigma-to-half-width conversion | §2.1 gives about 0.04 to 0.05 rad in half-width, an order of magnitude only, and notes that sigma = 0.10 corresponds to r of about 0.17 |
| 16 | optional | Qubit range of the reset-dissipation precedents | Bottom line and §3.3 now read 100 to 139 qubits; Tirado et al. used 86 emitters on 129 qubits |
| 17 | optional | Sulimov and Lehmann's setting was misdescribed | §4.2 now describes the discrepancy model, the mirror circuits and the held-out sizes of 10 to 20 qubits; the lesson transfers by analogy |
| 18 | optional | Scope of the Gehér et al. result, and the shot figure | §6 scopes the result to their noise model (resets bring no benefit in memory experiments) and corrects the figure to about 1.8e7 shots per setting for a two-setting difference, next to the pre-registered floors |
| 19 | optional | The Arute et al. figures needed qualifying | §4.1 gives means and medians and the per-layer-pattern simultaneity, and uses the per-cycle factor 1.43 as the closer analogue of kappa |
| 20 | optional | Rationale for l = 4 inherited from the rejected law discrimination | Item 2 now says that l = 4 completes the pre-registered point and is expected to be an upper bound. §3.1 adds the p = 0.25 finding as further support for item 3 |
| 21 | optional | Minor attributions | §2.4: about 30 % with item 7 alone, item 6 protective. §2.3: Leviatan et al. relied on a validation hierarchy, and "surrogate-limited" is the track's template. §3.2: H7 sits in Section 3b Hypotheses and c in Channel |

**Left open by the reviewer** (carried into §9 of version 2):

- the Corollary 2 numbering in the PRX version of Schuster et al.;
- the version differences behind the Schuster and Yao and Chen et al. ONOS rows;
- the IBM blog figures;
- the content of the framing-only hardware papers;
- the consolidated CSV's identifiers beyond the map's 31 DOIs and 19 arXiv ids;
- the n = 60 pre-drawn H7 curve.
