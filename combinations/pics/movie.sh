#!/bin/sh

rm -f mcmc.mp4

# ffmpeg  -i pic_%04d.png -framerate 500 -map 1:0 -map 0:0 -strict -2 -vcodec libx264 -preset slow -vb 500k -maxrate 500k -bufsize 1000k -vf 'scale=-1:480 ' -threads 0 -ab 64k -s 640x480 -movflags +faststart -metadata:s:v:0 rotate=0 -fflags +genpts output.mp4
ffmpeg -framerate 500 -i  %04d.png mcmc.mp4
ffmpeg -framerate 500 -i  %04d.png mcmc.webm
ffmpeg -framerate 500 -i  %04d.png mcmc.avi

# scp mcmc.webm smodels.hephy.at:/var/www/walten/
