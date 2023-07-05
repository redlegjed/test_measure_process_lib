TMPL Advanced usage
===================

This page describes some of the more advanced features of TMPL.

* *Data*: Where data can be stored in TMPL objects
* *Resources* : Adding extra resources
* *Processing* : How to add processing to a *Measurement* class using the *process()* method
* *Customisation*: Using custom configuration for *Measurements*
* *Services* : Make common functions available to all objects in a test sequence
* *Sequencing* : How to make *Measurements* execute only under certain conditions or stages of the sequence


Data
-----
TMPL objects have several internal data structures that can be used for static and temporary storage. These are the following:

* *config*: static storage, usually defined in the object's *initialise* method. *config* is intended for configuration settings that are set once per sequence run.
* *local_data*: storage structure local to measurements and conditions. This can be used to store temporary data that is local to a *Measurement* or *SetupCondition*.
* *global_data*: temporary storage available to all measurements and conditions. *global_data* provides a way for different measurements and conditions in a sequence to pass data between each other. It should be used with care because relying on it will make objects less modular.

All of these data structures are objects of the class *ObjDict*. This means they are basically dictionaries. They have all the same methods as a dictionary. The main difference is that the keys can be specified using the dot,'.', notation. Some examples are shown below:

.. code-block:: python

    # Set/get a flag
    test_seq.config.flag = True
    flag = test_seq.config.flag 

    # Change number of averages in a measurement
    test_seq.meas.Current.config.ammeter_averages = 16

    # Set global data in test sequence
    test_seq.global_data.my_name = 'fred'

    # Read back global data in measurement
    name = test_seq.meas.Current.global_data.my_name

    # Set local data in measurement
    test_seq.meas.Current.local_data.timer_count = 1

Adding extra resources
-----------------------
*resources* are usually added as a dictionary when a TMPL class is instantiated. Each item in the dictionary is added as a property to all TMPL classes under the main *TestManager* object. 

There may be occasions where a resource is generated inside a TMPL class, e.g. a Measurement class, and is required to be available to other classes. An example might be an object that is created at the start of a test sequence, like creating a test instrument object.

In this case, all TMPL classes have a method for adding resources dynamically, *add_resources*. Passing a dictionary to this method will automatically make new properties in all TMPL class objects in the test sequence. The properties will take the names of the dictionary keys, so these must be in a suitable form, i.e. no spaces.

This code shows an example of using *add_resources* to make a server object at the start of a sequence:

.. code-block:: python
    
    class ConnectToServer(tmpl.AbstractMeasurement):
        """
        Connect to server at start of test sequence

        """

        def initialise(self):
            self.run_on_startup(True)

            # Set up configuration values
            self.config.ip_address = '10.192.145.10'
            

        def meas_sequence(self):
            """
            Create server object and make it a resource for all 
            other classes
            """
            # Make server
            server_obj = make_server(self.config.ip_address)

            # Add server to resources of all TMPL objects in sequence
            self.add_resources({'server':server_obj})



Processing
----------
*Measurement* objects can have an optional method, *process()*, which if defined in the class will be called automatically after *meas_sequence()*. This method is intended for processing data that has been measured in *meas_sequence()*. Like *meas_sequence()* there are no restrictions on what can be done in *process()* its name is just a guideline.

Here is an example of a *Measurement* class that includes a *process()* method:

.. code-block:: python

    class VoltageSweeper(tmpl.AbstractMeasurement):
        """
        Example of a Measurement that adds its own coordinates and has
        a process method

        Measurement method:

        * Sweep voltage
        * Measure current at each voltage step
        * Process voltage and current to calculate resistances

        """
        name = 'VoltageSweep'

        def initialise(self):

            # Set up the voltage values to sweep over
            self.config.voltage_sweep = np.linspace(0,1,10)
            
        def meas_sequence(self):
            
            #  Do the measurement
            
            current = np.zeros(self.config.voltage_sweep.shape)

            for index,V in enumerate(self.config.voltage_sweep):
                # Set voltage
                self.voltage_supply.set_voltage(V,self.resistor)

                # Measure current
                current[index] = self.resistor.current_A

            
            # Store the data
            self.store_coords('swp_voltage',self.config.voltage_sweep)
            self.store_data_var('current_A',current,coords=['swp_voltage'])

            # Debug point
            self.log('finished sweep')


        @tmpl.with_results(data_vars=['current_A'])
        def process(self):

            # Get measurement data for current set of conditions
            ds = self.current_results

            # Fit a line to current vs voltage
            p = ds.current_A.polyfit('swp_voltage',1)

            # Get resistance from slope of line
            resistance_ohms = p.polyfit_coefficients.sel(degree=1).values

            # Store data into self.ds_results
            self.store_data_var('resistance_ohms',[resistance_ohms])


The *process()* method in the example makes use of several TMPL features:

* The *@tmpl.with_results* decorator is used to ensure that the data required for processing is present in the *self.ds_results* Dataset.
* The *current_results* property is used to pull data from the last run of *meas_sequence()* into a local *xarray* Dataset that only contains data for the current *SetupConditions*.
* The actual calculation makes use of *xarray* polynomial fitting to fit a line and get its slope.
* Finally the result is store into *self.ds_results* using the *store_data_var()* method.

Like any other method in the class *process()* can also access data in the other data storage properties: *config*, *local_data* and *global_data*. These can all be used for passing data between methods.

The *process()* method can also be used as a top level method that calls other processing methods or functions.

.. code-block:: python

    def process(self):
        """
        Top level process method, call other method to do
        actual processing

        """
        self.process_convert_degC_to_degK()
        self.process_smooth_data()
        self.process_curve_fit()

    def process_convert_degC_to_degK(self):
        # :

    def process_smooth_data(self):
        # :

    def process_curve_fit(self):
        # :


Processing only classes
++++++++++++++++++++++++
There is no specific class for purely processing data. This is because it would just be the same as a *Measurement* class. However if you want to make a processing only class then it can either be done the same way as any other *Measurement* class, using the *meas_sequence()* method as the top level code or by creating an empty *meas_sequence()* and putting the main code in the *process()* method as in this example:

.. code-block:: python

    class ProcessOnly(tmp.AbstractMeasurement):

        def meas_sequence(self):
            # Empty method
            pass

        def process(self):
            # Main code goes here
            # :


Post processing
++++++++++++++++
If post-processing is required after all measurements have been executed over all conditions then the class can be tagged to run only at the end in the teardown stage. 


.. code-block:: python

    class PostProcess(tmp.AbstractMeasurement):

        def initialise(self):
            # Tag this class to run only at the end
            self.run_on_teardown(True)

        def meas_sequence(self):
            # Empty method
            pass

        def process(self):
            # Main code goes here
            # :


Customisation
-------------
All the TMPL objects have a *.config* property. From its name it is intended to hold configuration data. This is usually static values that are required for performing measurements or processing.


.. code-block:: python

    class CustomisableMeasurement(tmpl.Measurement):

        def initialise(self):

            # Add customisable parameters to self.config
            self.config.number_averages = 16
            self.config.ammeter_range_A = 0.01


        def meas_sequence(self):
            # Use config setting in measurement

            # Instrument setting
            self.ammeter.range_A = self.config.ammeter_range_A

            # Measurement setting
            readings = []
            for n in self.config.number_averages:
                readings.append(self.ammeter.read_current())

            ave_current = np.mean(readings)


The values defined in *.config* should be regarded as defaults. When running the *Measurement* from a *TestManager* sequence the values in *.config* can be changed for experimentation. For example if the *CustomisableMeasurement* class above were to be run from a *TestManager* sequence called *seq* then the *.config* settings can be changed by accessing them through the *TestManagers* *meas* property.

.. code-block:: python

    # Change a config value from TestManager object
    seq.meas.CustomisableMeasurement.config.number_averages = 4


Global configuration
+++++++++++++++++++++
Setting configurations through each *Measurement* object may not always be desired, especially if *Measurement* objects share a common configuration value. For this reason  *TestManager* objects have *.config* properties that will be copied to all *Measurement* and *SetupCondition* objects when the *TestManager* object is created.


.. code-block:: python

    class SeqWithGlobalConfig(tmp.AbstractTestManager):
        """
        Test sequence that defines global config settings

        """

        def initialise(self):
            # Define global config settings here
            self.config.length_units = 'cm'
            self.config.storage_path = '/home/experimental_data'


        def define_setup_conditions(self):
            # :

        def define_measurements(self):
            # :


Another way to define global configuration settings is to pass a dictionary into the *TestManager* object when creating it. The contents of the dictionary will be copied into the *.config* property of the *TestManager* and all *Measurement* and *SetupCondition* objects contained inside it.

.. code-block:: python

    # Config values defined in external dict
    my_config = {'serial_number':'B345',
                'lab_name':'Maxwell_House'}

    # resources
    my_res = {'voltmeter':voltmeter_object}

    # Pass config values as optional input argument
    test_seq = SeqWithGlobalConfig(my_res,config=my_config)

    # Access config values from TestManager object
    test_seq.config.lab_name

    # or measurement objects
    test_seq.meas.VoltageSweep.config.serial_number

    # or SetupCondition objects
    test_seq.conditions.temperature.config.lab_name

The global config settings will also be available at the individual class level from *self.config*, for example:

.. code-block:: python

    self.config.lab_name
    self.config.serial_number

Values passed in through a dictionary as shown above will **overwrite** config values with the **same name** defined locally in the classes. This is useful if several *Measurement* or *SetupCondition* classes rely on the same config setting. The default values can be defined locally in the class and overwritten by passing in a dictionary with same name as the local classes. The *serial_number* property in the code above is a good example of this. Many classes may want to know this value. The code below shows how this might work:

.. code-block:: python

    # Measurement classes
    class Meas1(tmpl.AbstractMeasurement):

        def initialise(self):
            self.config.serial_number = 'default_ser_num'

        # :

    class Meas2(tmpl.AbstractMeasurement):

        def initialise(self):
            self.config.serial_number = 'default_ser_num'

        # :


    class TestSequence(tmpl.AbstractTestManager):

        def initialise(self):
            self.config.serial_number = 'default_ser_num'

        # :

    # Set serial number for all objects in test sequence
    my_config = {'serial_number':'AG678'}
    seq = TestSequence(resources,config=my_config)



Services
---------

Services are functions that can be accessed by any of the TMPL objects. For example a service might be a function to convert metres into centimetres called *m_to_cm*. This would be called from inside a TMPL object like this:

.. code-block:: python

    length_cm = self.services.m_to_cm(length_m)

Services can be added in the following ways:

* Adding in the *define_services()* method of the *TestManager* class
* Tagging methods in *Measurement* or *SetupCondition* classes using the decorator *@tmpl.service*

These are described in more detail in the following sections.



Adding Services to *TestManager* class
+++++++++++++++++++++++++++++++++++++++

Services can be added globally to the *TestManager* class using the optional method *define_services()*. Services are basically functions and can be added directly to the *.services* property of the *TestManager* as shown in this example


.. code-block:: python

    # Define a function to use as a service
    def percent(fraction):
        return 100*fraction


    class ExampleTestSequence(tmpl.AbstractTestManager):

        def define_setup_condition(self):
            # ...

        def define_measurements(self):
            # ...


        def define_services(self):
            """
            Define service functions

            """

            # Add service as function reference
            self.services.percent = percent

            # Or lambda function
            self.services.meters_to_cm = lambda m: m*100

            # dict style
            self.services['kg_to_g'] = lambda kg: kg*1000


Services defined in *define_services* should be stand alone functions. However services can also be derived from *Measurement* or *SetupCondition* classes as described next.

Services from *Measurement* and *SetupCondition* classes
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Sometimes data generated or measured in one *Measurement* or *SetupCondition* class is useful in another class. For example a *Measurement* class may take a series of readings that act as a look up table for other *Measurement* classes. This data could be pushed into the *ds_results* Dataset or *global_data* or *local_data* so other classes could access it. In the case of a look up table each class that wanted to use it would have to implement its own code for cross referencing through the table. It would be more convenient if the class that generated the look up table could provide a "service" that implements the cross referencing code. Then other classes can just call the service function. This can be done by tagging class methods with the *@tmpl.service* decorator.

Any class method can be tagged using the *@tmpl.service* decorator to turn it into a service. The following example shows one class creating a service and another class using it.

.. code-block:: python

    class MeasurementWithService(tmpl.AbstractMeasurement):
        """
        This measurement class takes some readings and makes the results
        available for others via a service called "lut_lookup"
        """

        def meas_sequence(self):
            # Top level measurement sequence
            # Takes readings that are logged into a table in self.local_data

            # Measurement code
            # ...
            
            # Store data locally
            self.local_data.lut_dict = lut_measured

        @tmpl.service
        def lut_lookup(self,key_value):
            """
            Provide a lookup service to other classes

            Parameters
            -----------
            key_value: str
                key to cross reference in lookup table
            """
            return self.local_data.lut_dict[key_value]



    class MeasurementUsingService(tmpl.AbstractMeasurement):
        """
        This measurement uses the "lut_lookup" service
        """
        def initialise(self):
            self.config.lut_key = 'chamber_id'
        
        @tmp.with_service(['lut_lookup'])
        def meas_sequence(self):

            # Get value from lookup table
            self.services.lut_lookup(self.config.lut_key)

            # Measurement code
            # ...

In the example the second *Measurement* class that uses the service has a decorator *tmpl.with_service*. This accepts a list of service names. The decorator just checks if the services listed are available and if not will throw an error. The *with_service* decorator is entirely optional, it just adds a layer of robustness.

Alternatively the services available can be checked at any time by checking the property *services_available* which is a list of service names. For the lookup table example this might be something like:

.. code-block:: python

    if 'lut_lookup' not in self.services_available:
        raise RuntimeError('No service')


Although this section has presented all the examples using *Measurement* classes, the same can be used from within *SetupCondition* classes as well.

Sequence states
----------------

When a *TestManager* sequence is executed using the *run()* method it creates a loop. Before starting the loop a table of setup conditions is created. Each row of the table represents a combination of setup conditions. Each iteration of the loop is one row of the table. Within this loop there are particular states where *Measurement* classes can be executed. These states are *Startup*, *Setup*, *Main*, *After*, *Teardown* and *Error*. The sequence loop runs in the order below, with the states shown in **bold**.

* Build setup conditions table
* **Startup** : Run anything that needs setting up
* Load first set of conditions from table
    - **Setup** stage
    - For each condition in the set
        + Set condition to current value
        + Run any measurements for this condition
    - **Main** : Run main measurements
    - **After** : Run teardown for current set of conditions
* **Teardown**: Run global teardown measurements, e.g. shutdown, store results
* **Error** : Run when error occurs.

*Measurement* classes can be set to execute in one or more of these states using methods with the prefix *run_*.

* *run_on_startup* : Run before any conditions have been set at the **Startup** state
* *run_on_setup* : Run after a specific condition has been set in the **Setup** state
* *run_on_main* : Run in the main loop. This is the default state and does not need to be explicitly set.
* *run_after*: Run after all main measurements have been executed for one set of conditions.
* *run_on_teardown*: Run at the end of the sequence. This is useful for shutting down.
* *run_on_error*: Run when an error occurs



Sequencing example
++++++++++++++++++++
This section will go through an example of sequencing measurements. We will start with the *TestManager* definition for the simple resistor measurement.

.. code-block:: python

    class ExampleTestSequence(tmpl.AbstractTestManager):
        """
        Example test sequence

        Runs a dummy measurement sequence over temperature and humidity conditions.

        Measurement sequence is:

        * Turn on equipment
        * Wait for stabilisation
        * Run a voltage sweep
        * Turn off equipment

        """
        name = 'ExampleResistorTest'

        def define_setup_conditions(self):
            """
            Add the setup conditions here in the order that they should be set
            """

            self.add_setup_condition(TemperatureConditions)
            self.add_setup_condition(HumidityConditions)


        def define_measurements(self):
            """
            Add measurements here in the order of execution
            """

            # Setup links to all the measurements
            self.add_measurement(TurnOn)  # Run on startup
            self.add_measurement(Stabilise) # Run after temperature is set
            self.add_measurement(VoltageSweeper) # Run in main loop
            self.add_measurement(TurnOff) # Run on teardown

            # Go here if errors occur
            self.add_measurement(HandleError) # Run on error


Looking at the *define_measurements()* method at the end of the class definition, the comments indicate where we want each *Measurement* class to run. There are two ways to set when *Measurement* classes run:

Set run state in class definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first method is to set the run state from within the *Measurement* class definition itself. The code below shows the class definitions for *TurnOn*, *TurnOff*, *Stabilise* and *HandleError*. For each class the run state is set in the *initialise()* method.

.. code-block:: python

    class TurnOn(tmpl.AbstractMeasurement):
        """
        Turn on all equipment
        """

        def initialise(self):
            self.run_on_startup(True) # <- Set run state


        def meas_sequence(self):
            self.log('TurnOn measurement')


    class TurnOff(tmpl.AbstractMeasurement):
        """
        Turn off all equipment
        """

        def initialise(self):
            self.run_on_teardown(True) # <- Set run state


        def meas_sequence(self):
            self.log('TurnOff measurement')


    class HandleError(tmpl.AbstractMeasurement):
        """
        Handle any errors generated
        e.g. shut off critical equipment, store data etc
        """

        def initialise(self):
            self.run_on_error(True) # <- Set run state

        def meas_sequence(self):
            self.log('Error handler')
    

    class Stabilise(tmpl.AbstractMeasurement):
        """
        Wait for stabilisation
        - only run this after temperature has be set
        """

        def initialise(self):
            # Run in the "Setup" stage only after 
            # temperature has been set
            self.run_on_setup('temperature_degC')

        def meas_sequence(self):
            self.log('Stabilising')


Setting the run state is mostly a boolean operation. However when using *run_on_setup* the name of the condition is specified. This is the value of the *name* property of the *SetupCondition* class. If *name* was not specified in the class definition then it will default to the class name. In the example above it is assumed that *name* in the *TemperatureConditions* class is "temperature_degC".


Set run state from *define_measurements*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
An alterative way to set the run state is from inside the *TestManager* class definition. This is better if the same *Measurement* class is reused in different sequences where it might be required to run in different states.

Here is a revised version of the *define_measurements* method with the run state settings added:

.. code-block:: python


    def define_measurements(self):
        """
        Add measurements here in the order of execution
        - Also add the run state of each measurement
        """

        # Setup links to all the measurements
        self.add_measurement(TurnOn,run_state=self.RUN_STAGE_STARTUP)

        self.add_measurement(Stabilise,
                                run_state={self.RUN_STAGE_SETUP:'temperature_degC'})

        # Runs in main loop no need to set state
        self.add_measurement(VoltageSweeper) 

        self.add_measurement(TurnOff,run_state=self.RUN_STAGE_TEARDOWN)

        # Go here if errors occur
        self.add_measurement(HandleError,run_state=self.RUN_STAGE_ERROR)


The *define_measurements* method has an optional keyword argument *run_state* which takes a string, list or dict as the input. For convenience the string values are all properties of the *TestManager* class with the prefix *RUN_STAGE_*. They are listed below:

.. code-block:: python

    # Run stages
    # These labels are used to reference all the stages where a measurement
    # can be run
    RUN_STAGE_STARTUP = 'STARTUP'
    RUN_STAGE_TEARDOWN = 'TEARDOWN'
    RUN_STAGE_SETUP = 'SETUP'
    RUN_STAGE_MAIN = 'MAIN'
    RUN_STAGE_AFTER = 'AFTER'
    RUN_STAGE_ERROR = 'ERROR'

    