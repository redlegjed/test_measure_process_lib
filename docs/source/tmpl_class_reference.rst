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
    resources = {'ammeter':ammeter_object,'voltmeter':voltmeter_object,'chamber':chamber_object}

    # Create test sequence object
    test_seq = ResistanceMeasureSequence(resources)

    # Run the test
    test_seq.run()

    # Store test data
    test_seq.save(filename)

Test code usually needs *resources*. This can be anything, the obvious examples are objects that allow access to test instruments, as illustrated in the example above. The *resources* dictionary that is passed in as the main argument of the *TestManager* class will be made available to all *SetupCondition* and *Measurement* classes so they can use them in their own methods. The dictionary keys should adhere to Python variable naming conventions because they will be made into properties of the *TestManager*, *SetupCondition* and *Measurement* classes. In our example all our classes will have *.ammeter*, *.voltmeter* and *.chamber* properties.

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

Definition
+++++++++++

*Measurement* classes are responsible for executing the code that takes a specific measurement or multiple measurements. They inherit from the *AbstractMeasurement* class. *Measurement* classes require one mandatory method, *meas_sequence*. This can either contain all the measurement code or, more usually, it can be the top level that calls other class methods in a sequence. The example below shows a simple *Measurement* class for reading electrical current from an ammeter.

.. code-block:: python

    class Current(tmpl.AbstractMeasurement):
        """
        Measure current with ammeter

        """
            
        def meas_sequence(self):
            """
            Mandatory method for Measurement classes

            Performs the actual measurement and stores data.
            """
            #  Measure current with ammeter
            current = self.ammeter.current_A

            # Store the data
            self.store_data_var('current_A',current)


In the example the *Current* class only has the mandatory *meas_sequence* method. It also assumes there is a property *ammeter* available, which should have been passed in as a *resource* to the *TestManager*. The *ammeter* object is used to measure the electrical current. How it does this will depend on how the object has been defined outside TMPL. In this case it is assumed that it has a property *current_A* that returns a single value.

The next line stores the measured value into the class internal storage. This will be discussed in more detail in :ref:`Storing data <label-storing-data>` below.


Initialisation and configuration
++++++++++++++++++++++++++++++++

*Measurement* classes can also have an optional *initialise* method, similar to *SetupCondition* classes. This is generally used to define configuration options for the measurement. The example below shows a revised *Current* class that uses the *initialise* method to define some configuration values for the *ammeter*.


.. code-block:: python

    class Current(tmpl.AbstractMeasurement):
        """
        Measure current with ammeter

        """
        def initialise(self):
            """
            Set configuration options
            """
            self.config.ammeter_range_A = 2.5
            self.config.ammeter_averages = 8

            
        def meas_sequence(self):
            """
            Mandatory method for Measurement classes

            Performs the actual measurement and stores data.
            """
            # Setup
            self.configure_ammeter()

            #  Measure current with ammeter
            current = self.ammeter.current_A

            # Store the data
            self.store_data_var('current_A',current)


        def configure_ammeter(self):
            """
            Setup the ammeter with configuration options
            """
            self.ammeter.range = self.config.ammeter_range_A
            self.ammeter.averages = self.config.ammeter_averages

*Measurement* classes have a property, *config*, which is basically a dictionary that can be used to store any kind of data. This data is only accessed by the user defined methods. None of the internal workings of the *AbstractMeasurement* class use it.

*config* is an internal *TMPL* class called *ObjDict*. It is a dictionary where the keys are also properties. Thus data can be added in two ways:

.. code-block:: python

    # property style access
    self.config.ammeter_range_A = 2.5

    # Dict style access
    self.config['ammeter_range_A'] = 2.5

*config* is also available from the *Measurement* object once it has been created by the *TestManager*. *Measurement* objects are available from the *TestManager* through the *.meas* property.

.. code-block:: python

    # Create test sequence object
    test_seq = ResistanceMeasureSequence(resources)

    # Change Current measurement configuration
    test_seq.meas.Current.config.ammeter_averages = 16




.. _label-storing-data:

Storing measurement data
+++++++++++++++++++++++++

Data variables
^^^^^^^^^^^^^^

*Measurement* classes store data into a property called *.ds_results*. This is an `xarray <http://xarray.pydata.org/en/stable/>`_ *Dataset* object. TMPL classes all have helper methods for storing data to Datasets. The simplest way to store data directly into *.ds_results* is to use the *store_data_var* method as seen in the examples above.

.. code-block:: python

    # Store the data
    self.store_data_var('current_A',current)



xarray *Datasets* have two main components: *coordinates* and *data variables*. *coordinates* are the independent variables, e.g. *x*, and *data variables* and dependent variables, e.g. *y = f(x)*. In the case of a *Measurement* class the independent variables are the *SetupConditions*. When *store_data_var* is called, it automatically makes a *data variable* in the *.ds_results* *Dataset* that has *coordinates* of the current *SetupConditions*. So in the example above, if the *SetupConditions* is *Temperature*, then the *current_A* *data variable* will have *Temperature*  as its *coordinate*. When the test sequence has been run *.ds_results* can be displayed. The standard *xarray* printout will show that *current_A* has a coordinate *Temperature*.


.. code-block:: python

    >>> test_seq.meas.Current.ds_results
    <xarray.Dataset>
    Dimensions:      (timestamp: 1, Temperature: 3)
    ...
    Coordinates:
    * timestamp    (timestamp) <U19 '2022-06-05 00h34m05'
    * Temperature  (Temperature) int64 25 35 45
    Data variables:
        current_A    (Temperature) float64 0.0 0.0 0.0

In this example the *Temperature* *SetupCondition* had default values of 25,35 & 45, so the *Current* measurement has been run at all those conditions. In each case the measured value was 0.0 as displayed in the printout.

Note the *timestamp* coordinate is added automatically by TMPL.


Coordinates and data variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Measurements will usually be more complicated than recording a single value. Frequently the measurement will have its own independent variables. The following *Measurement* class illustrates this by implementing a voltage sweep on the resistor. This requires stepping the voltage across the resistor over an array of values and recording the corresponding current for each voltage. In this case voltage is also an independent variable even though it is not a *SetupCondition*. The measurement also reads back the voltage from a *voltmeter* object that has been passed in as a *resource*.

.. code-block:: python

    class VoltageSweeper(tmpl.AbstractMeasurement):

        def initialise(self):

            # Set up the voltage values to sweep over
            self.config.voltage_sweep = np.linspace(0,1,10)
            

        def meas_sequence(self):
            
            #  Do the measurement
            
            current = np.zeros(self.config.voltage_sweep.shape)
            voltage = np.zeros(self.config.voltage_sweep.shape)

            for index,V in enumerate(self.config.voltage_sweep):
                # Set voltage
                self.voltage_source.voltage_set_V=V

                # Measure current
                current[index] = self.ammeter.current_A

                # Measure voltage across resistor
                voltage[index] = self.voltmeter.voltage_V

            
            # Store the data
            self.store_coords('swp_voltage',self.config.voltage_sweep)
            self.store_data_var('current_A',current,coords=['swp_voltage'])
            self.store_data_var('voltage_diff_V',voltage,coords=['swp_voltage'])

            # Debug point
            self.log('finished sweep')

The *current_A* and *voltage_diff_V* data variables are also dependent on the voltage being swept as well as the current conditions. To record this dependency the sweep voltage must be stored as a *coordinate* using the *store_coords* method. This takes a label and array or list as the input arguments. In this case it will create a new *coordinate* called *swp_voltage* that will appear in *.ds_results*.

To indicate that *current_A* and *voltage_diff_V* are also functions of the sweep voltage the optional argument *coords* is used with the *store_data_var* method. This takes a list of *coordinate* labels as its input. It can also take a dictionary, but that will be discussed later.

Now if *.ds_results* is printed the dependencies of the data variables can be seen:

.. code-block:: python

    >>> test_seq.meas.Current.ds_results
    <xarray.Dataset>
    Dimensions:          (timestamp: 1, Temperature: 3, swp_voltage: 10)
    Coordinates:
    * timestamp        (timestamp) <U19 '2022-06-05 01h21m43'
    * Temperature      (Temperature) int64 25 35 45
    * swp_voltage      (swp_voltage) float64 0.0 0.1111 0.2222 ... 0.8889 1.0
    Data variables:
        current_A        (Temperature, swp_voltage) float64 0.0 ... 9.857e-05
        voltage_diff_V   (Temperature, swp_voltage) float64 0.0 0.1111 ... 1.0

As well at *Temperature* the sweep voltage has been added as a *coordinate*. It is an array of 10 points, more than the *Dataset* printout will display. The data variables: *current_A* and *voltage_diff_V* now show the dependency as well.


Specifying individual coordinate values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TODO


Results data
------------
TODO

Modular Measurements
---------------------
TODO


