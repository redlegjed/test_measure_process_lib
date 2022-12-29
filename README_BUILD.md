# Building instructions

Cheatsheet for building for PyPi

## General
* Follows [python packaging tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
* *pyproject.toml* only accepts predefined [classifiers](https://pypi.org/classifiers/)




## Build for TestPypi

Building for the test version of pypi (recommended for flushing out problems with *pyproject.toml*).

```bash
# Go to top level directory
cd test_measure_process_lib

# Build tar files into dist/ directory
python -m build

# Upload to TestPypi
python -m twine upload --repository testpypi dist/*

```
Note this relies on having a token in the settings file *~/.pypirc*. This can be obtained by [registering with TestPypi](https://test.pypi.org/account/register/).


## Build for Pypi

Building for the real version of pypi.

```bash
# Go to top level directory
cd test_measure_process_lib

# Build tar files into dist/ directory
python -m build

# Upload to Pypi
python -m twine upload dist/*

```