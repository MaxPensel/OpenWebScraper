'''
Created on 15.06.2019

@author: Maximilian Pensel
'''
import sys
import os
import subprocess
import traceback

if len(sys.argv) >= 2:
    dir = sys.argv[1]
else:
    dir = None

# temporary script for testing, this will be replaced by the call to scrapy
command = ["python", "wait.py", "10", "2"]

try:
    subprocess.call(command)

    if not dir is None:
        os.removedirs(dir)
except Exception as exc:
    print(traceback.format_exc())
    print(exc)