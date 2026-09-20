# Manuscript skeletons (gradvar-phoenix)

Skeletons only. No hardware minute has been spent; every `[RESULT: ...]` and `[TBD: ...]` in the sources is a placeholder, and `grep -rn "placeholder\|tbd{" paper1 paper2` lists what remains to fill. Nothing in these files is a measured result.

| folder | content | class / style |
|---|---|---|
| `paper1/` | Pre-registered gradient-variance measurement on ibm_phoenix with the reset-dial arm (pre-registration v0.11.1, Deviations 14-42, H1-H7, Gates 1, 1b, 2) | revtex4-2, `prxquantum` (PRX Quantum / QST) |
| `paper2/` | 120-qubit reset / mid-circuit-measurement characterisation (pre-registration v0.4.3, Deviations 1-5, Q1-Q5) | revtex4-2, `pra` (PRA / QST) |
| `theory_companion/` | Outline only: second-moment calculation, theorems to prove or cite, data that feeds it. Theorist-delegated draft, for countersignature | article |
| `deviations.yaml` | Deviations 14-42 (Paper 1) and 1-5 (Paper 2), transcribed from the pre-registrations | data |
| `scripts/build_deviations_table.py` | renders `paper*/deviations_table.tex` from the YAML (`make tables`) | python3 + PyYAML |
| `Makefile` | `make check`, `make tables`, `make` (latexmk; skips the PDF step with a message when pdflatex is missing) | |

## Build

    make check      # which tools are present; validates the YAML
    make tables     # regenerate the Deviations tables
    make            # tables + PDFs, if pdflatex and latexmk are installed

The papers need `revtex4-2` (TeX Live `revtex` bundle), `booktabs`, `longtable` (wrapped in `\onecolumngrid` for the two-column `reprint` layout), `bbm`, `xcolor`, `hyperref`.

## Rules

* Results tables are keyed to the job-list point identifier (`patch, n, edge, L, k, resilience, shots, M`, the fields of `points[]` in `data/joblists/`); figure stubs carry the file names the analysis will write (`variance_vs_n_per_L`, `variance_vs_L_per_n`, `dial_variance_vs_p`, `prediction_vs_measured`; Paper 2: `q1_reset_error_map`, `q2_backaction_edges`, `q4_bloch_maps`, `q5_stability`).
* Pre-drawn predictions quoted in the tables come from `data/predictions/` at the commit named in each paper's provenance table (Gate 1 report of 20 Sep 2026); they are predictions, not results, and are provisional where the report says so.
* Citations: `references.bib` carries only entries whose arXiv id was resolved on export.arxiv.org on 2026-09-20 (title, authors, journal reference taken from there) or whose reading was verified page-by-page in `scratchpad/papers/verify_set_A.md` / `verify_set_B.md`. Entries marked `to be confirmed` lack an author list in the verification reports and must be completed from the journal page before submission.
* A new Deviation goes into `deviations.yaml` (after the pre-registration), never into the `.tex` tables by hand.
