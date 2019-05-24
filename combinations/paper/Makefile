all: compile

run:
	./model.py

draw:
	./drawPath.py

compile:
	latex document.tex

evince:
	evince document.pdf

show:
	mupdf document.pdf

edit:
	vim document.tex
	
clean:
	rm -rf document.log document.pdf document.aux document.out

.PHONY:
