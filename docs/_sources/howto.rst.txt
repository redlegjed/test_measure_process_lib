How to ...
===========

A collection or recipes for how to do various things in TMPL.


How to access measured data?
----------------------------
Measured data is stored in the *.ds_results* property of any TMPL object. Data from all measurements can be accessed from the top level *TestManager* object:

.. code-block:: python

    test_seq.ds_results

*.ds_results* is an `xarray <http://xarray.pydata.org/en/stable/>`_ *Dataset* object.

How to repeat a test sequence multiple times?
---------------------------------------------
Repeating a whole test sequence can be done multiple times by enabling the *Iteration* condition. This is a *SetupCondition* class that is populated by default but disabled. It is a counter where you set the number of iterations of the test sequence. To set multiple runs through the sequence follow the code below:

.. code-block:: python

    # Enable Iteration condition
    test_seq.conditions.Iteration.enable = True

    # Set iterations as a list, e.g. for 3 iterations
    test_seq.conditions.Iteration.values = [0,1,2]

    # For many iterations use a list comprehension
    test_seq.conditions.Iteration.values = [n for n in range(100)]

**WARNING** When iterating a whole sequence make sure that the code in the *Measurement* and *SetupCondition* classes can handle this, i.e. instrument settings are reset at the start of the sequence.

After the iterations have finished inspect the *test_seq.df_results* property. There will be a coordinate called *Iteration* for all measured data.

How to add a timestamp to *ds_results*
---------------------------------------
This is done automatically. A *Measurement* called *Timestamp* is always added to every test sequence.


How to repeat a Measurement multiple times in the same sequence?
-----------------------------------------------------------------

The same *Measurement* class can be used repeatedly, however it needs to be "tagged". This is done by using the optional *meas_names* argument in
the *add_measurement()* method.

The main problem with repeating *Measurements* is there will be a conflict with any data that is stored using *store_data_vars()* method. Since the
*Measurement* will always store under the same name. If the *meas_names* argument is used to tag each *Measurement*, as shown below, the contents of 
*meas_names* will be used as a prefix for any data stored using *store_data_vars()*.

.. code-block:: python

    class MeasureSequenceWithRepeats(tmpl.AbstractTestManager):
        """"
        Sequence with repeated Measurements
        """

    def define_setup_conditions:
        pass

    def define_measurements(self):
        """
        Add measurements here in the order of execution
        - Use "meas_names" to tag the same Measurement Class used multiple times
        """

        self.add_measurement(CheckTemperature,meas_name='Before')
        self.add_measurement(VoltageSweep)
        self.add_measurement(CheckTemperature,meas_name='After')


In this example, if the *CheckTemperature* class stores a data variable called *Temperature_degC*, then the final results will have two versions called:
*Before_Temperature_degC* and *After_Temperature_degC*.




