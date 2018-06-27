all: comp


ratioplots:
	./plotRatio.py -a CMS16050 -t T1tttt -c
	./plotRatio.py -a CMS16050 -t T2tt -c
	./plotRatio.py -a CMS16050 -t T5tctc -c
	./plotRatio.py -a CMS16052 -t T2bbWWoffSemiLep -c
	./plotRatio.py -a CMS16052 -t T6bbWWoffSemiLep -c
	./plotRatio.py -a CMS16050agg -t T1tttt -c
	./plotRatio.py -a CMS16050agg -t T2tt -c
	./plotRatio.py -a CMS16050agg -t T5tctc -c
	./plotRatio.py -a CMS16052agg -t T2bbWWoffSemiLep -c
	./plotRatio.py -a CMS16052agg -t T6bbWWoffSemiLep -c
	./plotRatio.py -a CMS16050best -t T1tttt -c
	./plotRatio.py -a CMS16050best -t T2tt -c
	./plotRatio.py -a CMS16050best -t T5tctc -c
	./plotRatio.py -a CMS16052best -t T2bbWWoffSemiLep -c
	./plotRatio.py -a CMS16052best -t T6bbWWoffSemiLep -c


labels:
	tex2im -o T2ttO.png '\mathrm{T2tt}'
	tex2im -o T2bbWWoffSemiLepO.png '\mathrm{T2bbWWoffSemiLep}'
	convert -rotate 270 T2bbWWoffSemiLepO.png T2bbWWoffSemiLep.png
	convert -rotate 270 T2ttO.png T2tt.png
	scp T2bbWWoffSemiLep.png T2tt.png smodels.hephy.at:/var/www/images/combination/

comp:
	latex comp.tex

edit:
	vim comp.tex
show:
	mupdf comp.pdf
