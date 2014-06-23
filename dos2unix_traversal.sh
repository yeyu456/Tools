#!/bin/bash
if [ -z  $1 ];then
    current_dir=$1
fi
if [ -z ${current_dir} ];then
    current_dir=`pwd`
fi
cd $current_dir
find ./ -path '*/.git/*' -prune -o -type f -print |xargs -l1 dos2unix 
