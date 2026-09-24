# Review record: Paper 1 upside memo (22 Sep 2026)

- **Document:** `paper1_upside_memo_2026-09-22.md`, version 1 (draft) reviewed; version 2 carries the fixes.
- **Reviewer:** independent reviewer sub-agent (did not write the memo), Claude Science session of 22 Sep 2026, checking against repository `main` at 369af38, the arXiv API and Crossref.
- **Verdict:** GO_WITH_CORRECTIONS. Two must-fix, eight should-fix and four optional corrections, all applied in version 2.
- **Scope the reviewer declared:** targeted parts of the pre-registration (Section 1 H1 to H4 openings; Section 3b Channel, H5 to H7, Grid, minute budget; Section 6 lines 184, 191, 195), not the whole file. Decision memo Section 5 was searched by keyword, and Sections 1 and 2 were read in full. HANDOVER Section 10, HANDOVER_MEMORY Sections 4 and 5, and reserve proposal Sections 04 to 06 were read in full. Papers were checked from metadata and abstracts only. Post-run reviews 03 and 04 and the day-3 lists were not opened.
- **Confirmed by the reviewer:**
  - The ledger: 44.67 spent, 315.33 left; cap 210 with 45 used.
  - About 61 min for the four waiting lists; 28.7 − 22.7 = 6.0 dial-arm minutes; the H7 design; blocks A to F at 55 to 65 (cap 100); about 105 minutes unbooked.
  - The day 1 and 2 results with both Deviation 19 flags.
  - The arithmetic: c = 0.583; e-fold 3.71 against 1.82 layers; std ≥ 0.0208.
  - All titles, venues and years.

| # | Severity | Correction | Addressed in version 2 |
|---|---|---|---|
| 1 | must fix | The odds were said to "agree" with earlier estimates that are qualitative or belong to other options; the Paper 2 Nature-family figure was misquoted | §1 item 1 and §6 rewritten: earlier estimates quoted as qualitative; new figures marked as new judgements; Paper 2 Nature family restored to 1 to 2 % per direction |
| 2 | must fix | The timing of the Option B Deviation relative to day 3's H5 and H7 readings was unstated | §4 B governance: adopt before review 06 reads H5 and H7, or declare the day-3 values used and fix the ℓ set and shots by a prior rule; day-3 H7 stays confirmatory |
| 3 | should fix | Resolvability at p = 0.25 was overstated ("decay curve", "quantitative law") | §4 B: both bounds, RMS and sigma at ℓ = 2, 4, 6, "ℓ = 2 likely, ℓ = 4 possible with more shots", "a modest strengthening, not a law" |
| 4 | should fix | ℓ = 4 at p = 0.5 is a contingent point restorable under the surplus rule, with no Deviation | §1 item 5 (a), §4 A and §7 item 1: restore the contingent dial items (about 1.9 min, ℓ = 4 +0.42); list coverage flagged as unverified |
| 5 | should fix | The surplus rule was paraphrased from the digest | §1 item 4 and §5: the three tiers quoted from pre-registration Section 6, "never to new arms without a Deviation" |
| 6 | should fix | Conditional odds were given without the probability of the condition | §6: unconditional row (about 5 to 8 %) and the reserve proposal's qualifier |
| 7 | should fix | Schmitt et al.'s overlap was understated: they attribute the effect to T1 non-unital noise | §1 item 2 and §3 row: T1 attribution, runtime scale, null model without an interval |
| 8 | should fix | 2603.27532 was mischaracterised | §3: own row, heuristic simulation-hardness near criticality, no gradient content; "none supplies a protocol" marked as a judgement |
| 9 | should fix | Option B pairing and drift | §4 B other cost: same jobs, one patch, same-day references, curves re-drawn on the placement; pre-specified paired statistic |
| 10 | should fix | "The only route to an unexpected result" was overstated | §1 item 5 and §4 A: "the most direct test of the two anomalies"; H5 and H6 can refute below the Deviation 33 floor |
| 11 | optional | Source c directly and cost Option B from the truncation-pair figures | §4 B: c from §3b Channel; about 3 min at 16,384 shots, 5 to 10 min with raised shots |
| 12 | optional | Bibliographic detail | §3 and §8: authors, volumes and article numbers; Mele "most circuits"; Cerezo data-acquisition proviso; two different Wang first authors |
| 13 | optional | Framing claims | §3: the surrogate baseline is for the n = 85 main-grid points, the dial arm's baseline is the pre-drawn curves; Nighthawk "first" hedged |
| 14 | optional | The binding date and the blocks A to F figures | §1 item 3: mid-November arXiv target; §4 C and §5: planning figure 73 and the cap raise |

**Left open by the reviewer:**
- Whether `day3_dial_refs.json` carries ℓ = 4.
- Schmitt et al.'s device list.
- Option B's exact minute cost (the budget model was not run).
- The day 1 and 2 results were checked against the handover digest only.
- The Option D explanation.
- The odds themselves, which are judgements.
