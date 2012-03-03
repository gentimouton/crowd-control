#!/bin/bash

# bash tuto: http://linuxconfig.org/Bash_scripting_Tutorial#9-bash-if--else--fi-statements

# check if enough arguments
if [ $# -lt 1 ]; then 
    echo "usage: ./bot.sh amount"
else
    export PYTHONPATH=$PYTHONPATH:`pwd`
    cd bot 
    echo "making $1 bots"

    # create args[1] bots
    for b in `seq 1 $1`; do
        echo "make bot #$b" 
        python3.2 main.py &
        sleep 1;
    done

fi


