# TMPL unit tests

This directory contains unit tests and examples of using TMPL.

## File descriptions

Generally filenames that being with 'test_' are unit tests. Other files are examples or support files.

The following is a list of the files in this directory and where they are used:

* _simple_resistor_example.py_ : The code used in the main README.md file for the "simple" example.
* _advanced_resistor_example.py_ : Advanced example used in main README.md
* _docs_example_resistor.py_ : Example code used in Class reference section of documentation
* _test_example_sequence.py_: Originally the main unit test of test sequences. It imports classes from *example_test_setup.py*.
* _test_example_resistor_test.py_: Later version of unit test that uses individual resources for instruments instead of station & testboard approach. This is a more generic example. Imports classes from *example_resistor_test.py*.
* _example_resistor_test.py_ : Individual resources for instruments.
* _example_test_setup.py_ : station & testboard based conditions & measurements