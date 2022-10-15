Getting Started
================

What is TMPL
------------

TMPL is a modular framework for running sequences of measurements and packaging up the acquired data into a convenient form.

The framework is designed to store data in the `xarray <http://xarray.pydata.org/en/stable/>`_ Dataset class. This provides a convenient structure for storing multi-dimensional data that can be easily visualised using libraries like `Holoviews <http://holoviews.org/index.html>`_ or its offshoot `hvplot <https://hvplot.holoviz.org/index.html>`_.

TMPL works by defining small modular classes for making individual measurements that can be combined together to make larger test sequences. The data acquired in each individual measurement can be 'scooped' up into one combined Dataset at the end of the test sequence for storing and analysis.

How it works
-------------

TMPL uses three types of class to define test sequences, test conditions and test measurements.

At the top level is the *TestManager* class which defines the sequence of measurements to be performed and the conditions that can be set for all the measurements. The *TestManager* class is usually very simple like the example here:

.. code-block:: python
    
    import tmpl

    class ResistanceMeasureSequence(tmpl.AbstractTestManager):
        """
        Measure resistance over temperature and humidity
        """

        def define_setup_conditions(self):
            """
            Add the setup conditions here in the order that they should be set
            """

            # Add setup conditions using class name
            self.add_setup_condition(Temperature)
            self.add_setup_condition(Humidity)

        def define_measurements(self):
            """
            Add measurements here in the order of execution
            """

            # Setup links to all the measurements using class name
            self.add_measurement(Resistance)

Here we are measuring the electrical Resistance at different temperatures and humidities. The *TestManager* class is declared based on the "template" class *AbstractTestManager*. Usually only two functions or methods need to be defined. *define_setup_conditions()* is used to set which test conditions are being set. The actual measurements are defined in the *define_measurements()* method.

The *self.add_setup_condition()* and *self.add_measurement()* methods of the *TestManager* take either a *SetupCondition* or *Measurement* class. These are the classes that access test instrumentation to do the real work of the measurement sequence.

A condition class might look like this:

.. code-block:: python

    class Temperature(tmpl.AbstractSetupConditions):
        """
        Set the temperature on the chamber.

        Assumes that there is a property called "chamber" that
        provides read/write control of the temperature.
        """

        def initialise(self):
            """
            Initialise default values and any other setup
            """

            # Set default values
            self.values = [25,35,45]

        @property
        def actual(self):
            """
            Read the current chamber temperature
            """
            return self.chamber.temperature_degC

        @property
        def setpoint(self):
            """
            Read the current chamber setpoint temperature
            """
            return self.chamber.temperature_setpoint_degC

        @setpoint.setter
        def setpoint(self,value):
            """
            Set a new temperature on the chamber
            """
            self.chamber.temperature_setpoint_degC = value

This example is for setting the temperature. By default it will set 25, 35 & 45 degC during the test sequence defined in the *TestManager* class. At each temperature all the measurements defined in *define_measurements()* will be run.

The measurements themselves are another class such as this one for resistance.

.. code-block:: python

    class Resistance(tmpl.AbstractMeasurement):
        """
        Simple resistance measurement using ohmmeter

        Assumes there is property, "ohmmeter", that gives read/write
        access to the ohmmeter instrument.
        """
            

        def meas_sequence(self):
            """
            Mandatory method for Measurement classes

            Performs the actual measurement and stores data.
            """
            #  Measure resistance with an ohmmeter
            resistance = self.ohmmeter.resistance_ohm

            # Store the data
            self.store_data_var('resistance_ohm',resistance)

*Measurement* classes require one mandatory method *meas_sequence()*. This will be executed at each test condition defined in *define_setup_conditions()*. *Measurement* classes can have many more methods, but *meas_sequence()* is the top level.

Once the *TestManager*, *SetupCondition* and *Measurement* classes are defined then the sequence object can be created and run.

.. code-block:: python

    # Get test instrument objects
    resources = {'ohmmeter':ohmmeter_object,'chamber':chamber_object}

    # Create test sequence object
    test_seq = ResistanceMeasureSequence(resources)

    # Run the test
    test_seq.run()

    # Store test data
    test_seq.save(filename)

Here test instrument objects are passed into the *TestManager* using a dictionary. The keys of the dictionary will be used to create a property in the *TestManager*, *SetupCondition* and *Measurement* classes. Thus 'ohmmeter' or 'chamber' can be accessed by any measurement or condition class without having to explicitly declare them.

Running the test sequence will activate a loop where each iteration will set one of each defined condition and execute the *Resistance* measurement. The actual order of setup conditions and measurements can be displayed before actually running the sequence using the property *df_running_order*

.. code-block:: python

    >>> test_seq.df_running_order
    
    @ ResistanceMeasureSequence | Generating the sequence running order
    @ ResistanceMeasureSequence | 	Running order done
        Operation           Label  Temperature  Humidity
    0     CONDITION     Temperature         25.0       NaN
    1     CONDITION        Humidity          NaN      55.0
    2   MEASUREMENT      Resistance         25.0      55.0
    3     CONDITION        Humidity          NaN      85.0
    4   MEASUREMENT      Resistance         25.0      85.0
    5     CONDITION     Temperature         35.0       NaN
    6     CONDITION        Humidity          NaN      55.0
    7   MEASUREMENT      Resistance         35.0      55.0
    8     CONDITION        Humidity          NaN      85.0
    9   MEASUREMENT      Resistance         35.0      85.0
    10    CONDITION     Temperature         45.0       NaN
    11    CONDITION        Humidity          NaN      55.0
    12  MEASUREMENT      Resistance         45.0      55.0
    13    CONDITION        Humidity          NaN      85.0
    14  MEASUREMENT      Resistance         45.0      85.0

*df_running_order* displays a table showing the order of operations during the test sequence. It shows when each condition is set and when each measurement is taken. Temperature was defined first in *define_setup_conditions*, so it is set first, then humidity. We have two humidity conditions for each temperature. The resistance measurement is performed after setting humidity. Then the next temperature is set and the cycle repeats.


Automatic code generation
---------------------------

To make it easier to create TMPL code there is an automatic code generation feature. This enables you to create a python module file (i.e. a .py file) with template code for the TMPL classes. 

The following code shows how to generate a module file:

.. code-block:: python

    import tmpl

    # Make lists of all the classes
    cond = ['Temperature','Humidity','Pressure']
    meas = ['VoltageSweep','CurrentSweep','PostProcess']
    managers = ['Calibrate','MainMeasure']

    # Give the module a name (full path accepted as well)
    name = 'BigExperiment.py'

    # Generate the code
    tmpl.make_module(name,conditions=cond,meas=meas,seq=seq)

    # Alternatively generate the code into a text string
    code_text = tmpl.make_module(name,conditions=cond,meas=meas,seq=managers,return_text=True)

Basically you give the *tmpl.make_module()* function lists of the names of the *SetupCondition, Measurement* and *TestManager* classes that you want in your file. It will then generate template code for each class and insert it into the file together with a standard doc string and imports.

Note that the order of the *SetupCondition* and *Measurement* class names will be used in the *TestManager* classes as the order in which conditions and measurements are executed. If this is not desired then they can be manually changed in the file later.





