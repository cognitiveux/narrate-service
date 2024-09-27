#!/bin/bash
pkill -9 celery
celery -A narrate_project worker & celery -A narrate_project beat & celery -A narrate_project flower --conf=./narrate_project/flowerconfig.py
sleep 5
