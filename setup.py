# setup.py

import pathlib
# import setuptools
from setuptools import find_packages, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# setuptools.setup()

setup(
    name="test_measure_process_lib",
    version="1.0.0",
    packages=find_packages(exclude=("unit_test",)),
    author="RedLegJed",
    author_email="rlj_github@nym.hush.com",
    license="Apache",
    # install_requires=["numpy","pandas", "xarray"],
    description="Test, Measure and Process library. Framework for lab experiments.",
    long_description=README,
)