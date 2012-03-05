#!/bin/bash

export PYTHONPATH=$PYTHONPATH:`pwd`
cd server
python3.2 cc_srv.py &

