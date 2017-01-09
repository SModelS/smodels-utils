all: ana sms
ana: ana_create ana_xsel
sms: sms_create sms_upload sms_move sms_xsel

ana_create:
	./listOfAnalyses.py 

ana_xsel:
	cat ListOfAnalyses | xsel -i

sms_create:
	./smsDictionary.py

sms_upload:
	scp *.png smodels.hephy.at:/var/www/feyn/

sms_move:
	mv *feyn* graphs/

sms_xsel:
	cat SmsDictionary | xsel -i
