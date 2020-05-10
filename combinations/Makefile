all: run

# a template talk about the topic
pdf:
	unoconv -o amb.pdf amb.odp

# create and update a proto-model on smodels.github.io/protomodels
# including the git-commit and git-push
hiscore:
	./plotHiscore.py -p -u github 

hiscore_submit:
	./plotHiscore.py -p -u github -c

# start ten typical workers from scratch
run:
	./walkingWorker.py --nmin 0 --nmax 10

doc:
	pyreverse *.py
	dot -Tps classes.dot -o outfile.ps

.PHONY:
