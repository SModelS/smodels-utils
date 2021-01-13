all: du-h

du-h: .PHONY
	du -h --max-depth=1 | tee du-h

.PHONY:
