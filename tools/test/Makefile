all: dot2tex

dot2tex:
	dot2tex test.dot > test.tex

compile:
	pdflatex test.tex

show:
	mupdf test.pdf

ps:
	latex -shell-escape doc.tex
	latex doc.tex

pdf:
	pdflatex -shell-escape doc.tex
	pdflatex doc.tex
