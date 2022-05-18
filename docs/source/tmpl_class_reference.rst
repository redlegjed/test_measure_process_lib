Class Reference
===============

This section describes the classes used by TMPL.

TestManager Class
-----------------


Definition
++++++++++

*TestManager* classes are the top level class that combines all the setup conditions and measurements together into one sequence. They all inherit from the *AbstractTestManager* class. The *AbstractTestManager* class requires that two mandatory methods be defined: *define_setup_conditions* and *define_measurements*, as shown in the example *TestManager* class below.


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
            self.add_measurement(Voltage)
            self.add_measurement(Current)
            self.add_measurement(Resistance)


*define_setup_conditions* consists of multiple calls to a method of *AbstractTestManager*, *add_setup_condition*. This takes as its argument a *SetupCondition* class. *SetupCondition* classes are described below in detail, but they contain the code that sets a single test condition, like temperature, humidity, voltage etc. The order that *SetupCondition* classes are added inside *define_setup_conditions* is important. It defines the order in which each condition is set. In the example below temperature is set first then humidity. This means that when the test is run, the first condition to be set will be temperature, then humidity. *SetupCondition* classes usually define a range of values for their specific condition. For example the *Temperature* class might define two temperatures, 25 and 40 degC, while the *Humidity* class might define three levels: 45,55,65 %. When the test sequence is run the *TestManager* class will extract all the values of temperature and humidity. It will then form a loop based on the order of *add_setup_condition* calls. So in this example the loop will run through the conditions in this order:

* Temperature: 25

    * Humidity: 45
    * Humidity: 55
    * Humidity: 65

* Temperature: 40
    
    * Humidity: 45
    * Humidity: 55
    * Humidity: 65

The other mandatory method required by *AbstractTestManager* is *define_measurements*. This operates in a similar way to *define_setup_conditions*, but this time it adds *Measurement* classes to the *TestManager*. The *add_measurement* method takes a *Measurement* class as its argument. The order in which the measurements are added will define the order in which they are executed. In the example the measurements are added in the order: Voltage, Current, Resistance. The *TestManager* class will remember that order and use it in combination with the conditions to generate a loop for executing the entire test sequence. The complete test sequence in our example will run in this order:

* Temperature: 25

    * Humidity: 45
    * Humidity: 55
    * Humidity: 65

        * Measure: Voltage
        * Measure: Current
        * Measure: Resistance

* Temperature: 40
    
    * Humidity: 45
    * Humidity: 55
    * Humidity: 65

        * Measure: Voltage
        * Measure: Current
        * Measure: Resistance

Running the test sequence
++++++++++++++++++++++++++

*TestManager* classes are used in the following way:

.. code-block:: python

    # Get test instrument objects
    resources = {'ohmmeter':ohmmeter_object,'chamber':chamber_object}

    # Create test sequence object
    test_seq = ResistanceMeasureSequence(resources)

    # Run the test
    test_seq.run()

    # Store test data
    test_seq.save(filename)

Test code usually needs *resources*. This can be anything, the obvious examples are objects that allow access to test instruments, as illustrated in the example above. The *resources* dictionary that is passed in as the main argument of the *TestManager* class will be made available to all *SetupCondition* and *Measurement* classes so they can use them in their own methods. The dictionary keys should adhere to Python variable naming conventions because they will be made into properties of the *TestManager*, *SetupCondition* and *Measurement* classes. In our example all our classes will have *.ohmmeter* and *.chamber* properties.

Once a *TestManager* object has been created, the sequence can be run with the *run* method. The sequence will then execute, printing out each condition and measurement as they run.

When the sequence has finished any results that have been stored can be saved using the *save* method and passing a filename. This should include the full path because no assumption is made about the storage location.

Accessing setup conditions and measurements
+++++++++++++++++++++++++++++++++++++++++++

When a *TestManager* object is created, it also creates objects for all the setup conditions and measurements using the *define_setup_conditions* and *define_measurements* methods. These objects are available from the *TestManager* object through the *.conditions* and *.meas* properties. For our example the objects would be available like this:

.. code-block:: python

    # Setup condition objects accessed through 'conditions' property
    test_seq.conditions.Temperature
    test_seq.conditions.Humidity

    # Measurement objects accessed through 'meas' property
    test_seq.meas.Voltage
    test_seq.meas.Current
    test_seq.meas.Resistance


SetupCondition Class
--------------------
TODO

Measurement Class
------------------
TODO

Results data
------------
TODO

Modular Measurements
---------------------
TODO


