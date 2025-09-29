PDF=main.pdf
TEX=main.tex

.PHONY: pdf clean arxiv

pdf:
	@if command -v latexmk >/dev/null 2>&1; then \
	  latexmk -pdf -bibtex -silent $(TEX); \
	else \
	  pdflatex -interaction=nonstopmode $(TEX) || true; \
	  bibtex main || true; \
	  pdflatex -interaction=nonstopmode $(TEX) || true; \
	  pdflatex -interaction=nonstopmode $(TEX) || true; \
	fi

clean:
	latexmk -C || true
	$(RM) -r dist

arxiv: pdf
	@mkdir -p dist/arxiv
	@cp -r sections figures references.bib main.tex dist/arxiv/
	@# Include the compiled .bbl for arXiv
	@cp -f main.bbl dist/arxiv/ 2>/dev/null || true
	@cd dist && zip -rq arxiv.zip arxiv
	@echo "dist/arxiv.zip を作成しました"
