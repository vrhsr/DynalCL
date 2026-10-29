PY ?= python3

.PHONY: all clean
all:
	$(PY) build.py

clean:
	latexmk -C main.tex || true
	rm -rf generated
