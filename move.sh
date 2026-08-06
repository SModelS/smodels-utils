#!/bin/sh

TAG="3.2.0"

git tag -d $TAG
git push origin :$TAG
git tag $TAG
git push origin $TAG
