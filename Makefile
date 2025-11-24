OUT=build
SRC=main.md

PANDOC_OPTS=--standalone --from=markdown+tex_math_single_backslash+raw_tex --to=latex \
	-V geometry:margin=1in \
	-V documentclass:article \
	-V fontsize=11pt \
	--citeproc \
	--pdf-engine=xelatex \
	--bibliography=refs.bib

.PHONY: all pdf tex clean

all: pdf

$(OUT):
	mkdir -p $(OUT)

pdf: $(OUT) $(SRC)
	pandoc $(SRC) $(PANDOC_OPTS) -o $(OUT)/main.pdf

tex: $(OUT) $(SRC)
	pandoc $(SRC) $(PANDOC_OPTS) -o $(OUT)/main.tex

clean:
	rm -rf $(OUT)
