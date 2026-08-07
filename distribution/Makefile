all: create

create:
	./createTarballs.py

deploy:
	cp database/database.tgz  ../../smodels-database-release
	cd ../../smodels-database-release && tar -xzvf database.tgz --strip-components=1 smodels-database/
