"""
Check over TMPL project
================================================================
Run some automated checks including the following:

* Version is the same between pyproject.toml and tmpl/__init__.py
* docs directory has a .nojekyll file
"""
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os
import pathlib
import tomllib
 
print('='*40)
print('Checking TMPL project')
print('='*40)

#================================================================
#%% Constants
#================================================================
BASEPATH = pathlib.Path(os.path.abspath('.'))
print(f'Basepath: {BASEPATH}')
 
#================================================================
#%% Check for .nojekyll file
#================================================================
jekyll_path = BASEPATH/'docs'/'.nojekyll'
if not jekyll_path.exists():
    print('No docs/.nojekyll file\nCreating one')
    jekyll_path.write_text('')

print('.nojekyll file exists.')


 
#================================================================
#%% Check versions between pyproject.toml and tmpl/__init__.py
#================================================================
# Read toml file
toml_file = BASEPATH/'pyproject.toml'
with open(toml_file, "rb") as f:
    data = tomllib.load(f)
    print('Read pyproject.toml')

import tmpl

# Compare versions
same = data['project']['version'] == tmpl.__version__
if not same:
    print('Version numbers different between pyproject.toml and tmpl.__version__')
else:
    print('Version numbers in sync')

 
 
print('='*40)
print('Checking done')
print('='*40)