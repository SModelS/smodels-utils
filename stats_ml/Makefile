all: fetch

count:
	wc -l full_slep/*csv
	wc -l full_chiwzoff/*csv

fetch:
	./fetch.sh

clean:
	find results -type f -mtime +1 -delete

clean_all:
	rm -f results/* slhafiles/*

backup:
	cp -r results_all results.no_s_min/ /groups/hephy/pheno/ww/
