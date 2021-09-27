all: tar

tar:
	tar czvf database.tgz smodels-database

upload:
	sshpass -f ~/.ssh/lxplus scp database.tgz lxplus.cern.ch:/eos/project-s/smodels/www/ADL/database210.tgz
	sshpass -f ~/.ssh/lxplus ssh lxplus.cern.ch 'cd /eos/project-s/smodels/www/ADL; ./create.py'
