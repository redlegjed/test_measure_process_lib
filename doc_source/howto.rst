How to ...
===========

A collection or recipes for how to do various things in TMPL.


How to access measured data
----------------------------
Measured data is stored in the *.ds_results* property of any TMPL object. Data from all measurements can be accessed from the top level *TestManager* object:

.. code-block:: python

    test_seq.ds_results

*.ds_results* is an `xarray <http://xarray.pydata.org/en/stable/>`_ *Dataset* object.

