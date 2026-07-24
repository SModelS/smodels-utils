all: fetch

fetch:
	scp -r clip-login-1:git/smodels-utils/stats_ml/\*_results .

clean:
	find results -type f -mtime +1 -delete

clean_all:
	rm -f results/* slhafiles/*

backup:
	cp -r results_all results.no_s_min/ /groups/hephy/pheno/ww/
