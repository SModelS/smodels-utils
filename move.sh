#!/bin/sh

TAG="3.0.3.post1"

git tag -d $TAG
git push origin :$TAG
git tag $TAG
git push origin $TAG
