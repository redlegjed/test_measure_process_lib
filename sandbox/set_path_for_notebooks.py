"""
Add tmpl path to sys.path for notebooks
"""
import pathlib
import os
import sys

BASEPATH = pathlib.Path(os.getcwd()).parent.parent
print(BASEPATH)
sys.path.append(str(BASEPATH))