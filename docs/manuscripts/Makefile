# Build the gradvar-phoenix manuscripts.
#   make            -> deviations tables + both papers + companion outline (needs latexmk and pdflatex)
#   make tables     -> only the auto-generated Deviations tables (needs python3 + PyYAML)
#   make check      -> report which tools are present; never installs anything
#   make clean
# The build stops with a plain message when pdflatex or latexmk is missing; it does not install TeX.
LATEXMK ?= latexmk
LATEXMKFLAGS ?= -pdf -interaction=nonstopmode -halt-on-error -file-line-error
PYTHON ?= python3

PAPERS := paper1 paper2 theory_companion
TABLES := paper1/deviations_table.tex paper2/deviations_table.tex

.PHONY: all tables check clean $(PAPERS)

all: tables $(PAPERS)

tables: $(TABLES)

$(TABLES): deviations.yaml scripts/build_deviations_table.py
	$(PYTHON) scripts/build_deviations_table.py

check:
	@$(PYTHON) scripts/build_deviations_table.py --check
	@command -v pdflatex >/dev/null 2>&1 && echo "pdflatex: $$(command -v pdflatex)" || echo "pdflatex: not installed (PDF build skipped; sources are still valid LaTeX)"
	@command -v $(LATEXMK) >/dev/null 2>&1 && $(LATEXMK) -v | head -1 || echo "latexmk: not installed"
	@kpsewhich revtex4-2.cls >/dev/null 2>&1 && echo "revtex4-2.cls: found" || echo "revtex4-2.cls: not found (install texlive-publishers or the revtex bundle)"

$(PAPERS): tables
	@if ! command -v pdflatex >/dev/null 2>&1 || ! command -v $(LATEXMK) >/dev/null 2>&1; then \
	  echo "skip $@: pdflatex/latexmk not installed (run 'make check')"; exit 0; fi
	cd $@ && $(LATEXMK) $(LATEXMKFLAGS) main.tex

clean:
	@for d in $(PAPERS); do (cd $$d && $(LATEXMK) -C main.tex >/dev/null 2>&1 || true; rm -f main.bbl main.run.xml); done
