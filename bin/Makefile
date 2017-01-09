all: create upload move xsel

create:
	./smsDictionary.py

upload:
	scp *.png smodels.hephy.at:/var/www/feyn/

move:
	mv *feyn* graphs/

xsel:
	cat SmsDictionary | xsel -i
