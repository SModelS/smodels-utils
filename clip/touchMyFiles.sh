#!/bin/bash

find /scratch/users/$USER/ -exec touch {} \;
echo Done touching scratch files
