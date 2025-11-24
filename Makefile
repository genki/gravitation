OUT=build
SRC=main.md
SRC_JA=main.ja.md

PANDOC_OPTS=--standalone --from=markdown+tex_math_single_backslash+raw_tex --to=latex \
	-V geometry:margin=1in \
	-V documentclass:article \
	-V fontsize=11pt \
	--citeproc \
	--pdf-engine=xelatex \
	--bibliography=refs.bib
PANDOC_OPTS_JA=$(PANDOC_OPTS) -V mainfont="Noto Sans CJK JP"

.PHONY: all pdf pdf-ja tex clean

all: pdf pdf-ja

$(OUT):
	mkdir -p $(OUT)

pdf: $(OUT) $(SRC)
	pandoc $(SRC) $(PANDOC_OPTS) -o $(OUT)/main.pdf

pdf-ja: $(OUT) $(SRC_JA)
	pandoc $(SRC_JA) $(PANDOC_OPTS_JA) -o $(OUT)/main.ja.pdf

tex: $(OUT) $(SRC)
	pandoc $(SRC) $(PANDOC_OPTS) -o $(OUT)/main.tex

clean:
	rm -rf $(OUT)
