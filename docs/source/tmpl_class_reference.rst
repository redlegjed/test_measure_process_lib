Class Reference
===============

Setting up a test sequence in TMPL requires creating three types of class:

* *Measurement* : These classes take the measurements, they are responsible for communicating with test equipment, acquiring the measurement data and storing it. A test sequence may have multiple *Measurement* classes attached to it. *Measure* classes always inherit from the *AbstractMeasurement* class defined by TMPL.
* *SetupCondition* : Classes that set the conditions under which measurements are made, e.g. temperature, voltage etc. They also interface with test equipment to set one specific condition, e.g. settting a temperature chamber to the required temperature. They always inherit from the *AbstractSetupCondition* class.
* *TestManager* : This class manages the test sequence. It contains multiple *Measurement* and *SetupCondition* classes that it puts together in a sequence. It is responsible for running this test sequence and collecting the data from all the individual *Measurement* and *SetupCondition* classes. 

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


*define_setup_conditions* consists of multiple calls to a method of *AbstractTestManager*, *add_setup_condition*. This takes as its argument a *SetupCondition* class. *SetupCondition* classes are described below in detail, but they contain the code that sets a single test condition, like temperature, humidity, voltage etc. The order that *SetupCondition* classes are added inside *define_setup_conditions* is important. It defines the order in which each condition is set. In the example above temperature is set first then humidity. This means that when the test is run, the first condition to be set will be temperature, then humidity. *SetupCondition* classes usually define a range of values for their specific condition. For example the *Temperature* class might define two temperatures, 25 and 40 degC, while the *Humidity* class might define three levels: 45,55,65 %. When the test sequence is run the *TestManager* class will extract all the values of temperature and humidity. It will then form a loop based on the order of *add_setup_condition* calls. So in this example the loop will run through the conditions in this order:

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

.. _running-test-sequence:

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

Definition
++++++++++

*SetupCondition* classes are responsible for setting and querying one specific condition. They all inherit from the *AbstractSetupCondition* class. This requires two mandatory properties: *actual* and *setpoint*, for reading the *actual* value of the condition and setting the value of the condition. *actual* and *setpoint* appear as properties of the *SetupCondition* class but usually they are *methods* that use the Python *@property* decorator to appear as properties. This is because querying and setting the condition usually requires interfacing to test equipment.

The code below shows an example of the definition of a *SetupCondition* class:

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

The *Temperature* class defines the required property/methods *actual* and *setpoint* using a temperature *chamber* object. *chamber* is an object that was supplied to the *TestManager* when it was created as a *resource* (see :ref:`running-test-sequence`). The *TestManager* will make all the objects passed in through *resources* available as properties in the *SetupCondition* objects.

The *Temperature* class definition above also includes a recommended method, *initialise*. *initialise* is intended for any custom initialisation required for setting the specific condition. It is also useful for defining the default range of *values* that the condition will take during the test sequence. In this example *initialise* is setting the *values* object to [25,35,45]. So by default, when the complete test sequence is run it will be performed at [25,35,45] degC. 

*SetupCondition* classes have a property, *values*, that is a list of the *setpoint* values that will be used in the test sequence when it is run. The *SetupCondition* class definition usually sets a default list for *values*. This can be customised later by direct access to the *values* property. When a *TestManager* runs the test sequence, it will scan each *SetupCondition* object in it's memory and extract the *values* list. It will then use these to build a table of test conditions that need to be set before performing each measurement.


Setting/Querying setup conditions
++++++++++++++++++++++++++++++++++

*SetupCondition* objects are created inside the *TestManager*. Once created they are available through the *TestManager* object. They can be used independently to set or query conditions without running in a test sequence.

.. code-block:: python

    # Condition is available through the 'conditions' property of TestManager object
    test_seq.conditions.Temperature

    # Read actual temperature
    test_seq.conditions.Temperature.actual

    # Read current setpoint
    test_seq.conditions.Temperature.setpoint

    # Set condition
    test_seq.conditions.Temperature.setpoint = 34.5



Measurement Class
------------------
TODO

Results data
------------
TODO

Modular Measurements
---------------------
TODO


