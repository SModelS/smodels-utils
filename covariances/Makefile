all: comp


ratioplots:
	./plotRatio.py -a CMS16050 -t T1tttt -c
	./plotRatio.py -a CMS16050 -t T2tt -c
	./plotRatio.py -a CMS16050 -t T5tctc -c
	./plotRatio.py -a CMS16052 -t T2bbWWoff -c
	./plotRatio.py -a CMS16052 -t T6bbWWoffSemiLep -c
	./plotRatio.py -a CMS16050agg -t T1tttt -c
	./plotRatio.py -a CMS16050agg -t T2tt -c
	./plotRatio.py -a CMS16050agg -t T5tctc -c
	./plotRatio.py -a CMS16052agg -t T2bbWWoff -c
	./plotRatio.py -a CMS16052agg -t T6bbWWoffSemiLep -c
	./plotRatio.py -a CMS16050best -t T1tttt -c
	./plotRatio.py -a CMS16050best -t T2tt -c
	./plotRatio.py -a CMS16050best -t T5tctc -c
	./plotRatio.py -a CMS16052best -t T2bbWWoff -c
	./plotRatio.py -a CMS16052best -t T6bbWWoffSemiLep -c

comp:
	latex comp.tex

edit:
	vim comp.tex
show:
	mupdf comp.pdf
