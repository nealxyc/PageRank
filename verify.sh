#!/bin/bash

#99 3.7220011692e-07
target=$1
if [[ -z $target ]]
then
  target="out.txt"
fi

line=$(head -n 100 $target | grep "99 ")
if [[ "$line" == "99 3.722"*"e-07" ]] 
then
  echo Correct.
else
  echo Wrong.
fi
