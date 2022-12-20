TMPL Application Programming Interface
======================================

.. module:: tmpl 

The core TMPL classes *TestManager*, *Measurement* and *SetupClasses* are all created from *abstract* class defintions. These are like "templates" that provide most of the underlying functionality, with only a few methods that need to be defined by the user.

TestManager classes
---------------------

*TestManager* classes are defined from the *AbstractTestManager* class and require the user to define the methods: *define_measurements* and *define_setup_conditions*. Optionally a *define_services* method can also be defined. The main methods that the user will encounter are documented below:

.. autoclass:: AbstractTestManager
    :members: define_setup_conditions, define_measurements, add_measurement, add_setup_condition, run, to_markdown, save, load

*Measurement* classes
-----------------------
*Measurement* classes are defined from the *AbstractMeasurement* class. They have one mandatory method that must be defined by the user: *meas_sequence*, plus two optional methods *initialise* and *process*.

.. autoclass:: AbstractMeasurement
    :members: initialise, meas_sequence, run, store_data_var, store_coords, ds_results_global, save, load


*SetupCondition* classes
--------------------------
*SetupCondition* classes are defined from *AbstractSetupCondition* class. They require the user to define two properties: *setpoint* and *actual*.

.. autoclass:: AbstractSetupConditions
    :members: initialise, setpoint, actual, ds_results_global


