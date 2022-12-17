TMPL Advanced usage
===================

This page describes some of the more advanced features of TMPL.

* *Data*: Where data can be stored in TMPL objects
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


Processing
----------
TODO


Customisation
-------------
TODO



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






Sequencing
++++++++++
TODO



