all: comp


ratioplots:
	./plotRatio.py -a CMS16050 -t T1tttt -c
	./plotRatio.py -a CMS16050 -t T2tt -c
	./plotRatio.py -a CMS16050 -t T5tctc -c
	./plotRatio.py -a CMS16052 -t T2bbWWoff -c
	./plotRatio.py -a CMS16052 -t T6bbWWoff -c
	./plotRatio.py -a CMS16050agg -t T1tttt -c
	./plotRatio.py -a CMS16050agg -t T2tt -c
	./plotRatio.py -a CMS16050agg -t T5tctc -c
	./plotRatio.py -a CMS16052agg -t T2bbWWoff -c
	./plotRatio.py -a CMS16052agg -t T6bbWWoff -c
	./plotRatio.py -a CMS16050best -t T1tttt -c
	./plotRatio.py -a CMS16050best -t T2tt -c
	./plotRatio.py -a CMS16050best -t T5tctc -c
	./plotRatio.py -a CMS16052best -t T2bbWWoff -c
	./plotRatio.py -a CMS16052best -t T6bbWWoff -c


labels:
	tex2im -o T2ttO.png '\mathrm{T2tt}'
	tex2im -o T2bbWWoffO.png '\mathrm{T2bbWWoff}'
	convert -rotate 270 T2bbWWoffO.png T2bbWWoff.png
	tex2im -o T6bbWWoffO.png '\mathrm{T6bbWWoff}'
	convert -rotate 270 T6bbWWoffO.png T6bbWWoff.png
	convert -rotate 270 T2ttO.png T2tt.png
	scp T6bbWWoff.png T2bbWWoff.png T2tt.png smodels.hephy.at:/var/www/images/combination/

comp:
	latex comp.tex

edit:
	vim comp.tex
show:
	mupdf comp.pdf
