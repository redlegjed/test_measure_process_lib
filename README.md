# Test, Measure, Process library (TMPL)

This library is a modular framework for running sequences of measurements. It is intended to provide a minimal boiler-plate code framework for writing measurement code in modules that can be linked together into test sequences. Although written for use in measurements the framework makes no assumptions about test equipment setup and is very generic. It could be used to make test sequences based on models or data analysis instead of actual measurements.

The framework is built around storing data in the [xarray](http://xarray.pydata.org/en/stable/) _Dataset_ class. This provides a convenient data structure for storing multi-dimensional data that can be easily visualised using libraries like [Holoviews](http://holoviews.org/index.html) or its offshoot [hvplot](https://hvplot.holoviz.org/index.html).

## Dependencies and installation
TMPL depends on these libraries. 

* [xarray](http://xarray.pydata.org/en/stable/)
* [pandas](https://pandas.pydata.org/pandas-docs/stable/)

TMPL can be installed locally by cloning the repository to a local folder and then installing with pip

```bash
cd <local_path>
git clone https://github.com/redlegjed/test_measure_process_lib.git
pip install -e <local_path>/test_measure_process_lib

```
Note that this does not install the dependencies. This is in case another package manager, e.g. Anaconda, is being used. So they have to be manually installed.



## Core classes

The framework is built on a set of core classes. These are built by inheriting from the Abstract classes defined in *tmpl_core.py*. The classes are:

* _TestManager_ classes: Based on _AbstractTestManager_ class. These classes run sequences of measurements over multiple setup conditions e.g. temperature, humidity etc. The _TestManagers_ are ultimately responsible for gathering up all data recorded during the sequence and packaging it into one xarray Dataset object.
* _Measurement_ classes: Based on _AbstractMeasurement_ class. These are the classes that actually perform the measurements. They are classes that can be run independently or in a sequence from a _TestManager_. The data that they collect and process is stored in an internal xarray Dataset object. When run from a _TestManager_ this dataset will be scooped up at the end of the sequence and added into the overall Dataset maintained by the _TestManager_.
* _SetupCondition_ classes: Based on _AbstractSetupCondition_. These classes are responsible for setting up experimental conditions e.g. temperature, pressure, supply voltage etc. They are small classes that have only one purpose, to set a specific condition. _TestManagers_ use _SetupCondition_ classes to set conditions during a sequence before running measurements. 


## Example usage

Before explaining the inner workings of the framework this section runs through a hypothetical example to show how the classes are used at the top level.

Suppose a _TestManager_ has been defined that has objects for setting *temperature and pressure*. It also has three measurement objects defined called *calibrate_scales, MeasureVolume and MeasureMass*.

The _TestManager_ is initialised with any _resources_ that the measurement classes require, e.g. instruments.

```python
# Define test equipment objects for measurements to use
# - can be anything that Measurement classes require
resources = {'chamber':chamber_object,
            'test_sample':test_sample_object,
            'instrument':instr_object}

# Create test manager object
test = TestManager_mymeas(resources)
```

Setup conditions under which test is to be run can be defined by accessing the _SetupConditions_ objects directly through the _setup_ property.

```python
test.setup.temperature.values = [25,40,75]
test.setup.pressure.values = [12,15,65]
```

The measurements to run during the sequence can be enabled/disabled by direct access to the _Measurement_ objects through the _meas_ property.

```python
test.meas.calibrate_scales.enable = False
test.meas.MeasureVolume.enable = True
test.meas.MeasureMass.enable = True
```

Now the sequence has been configured we can run the test over all setup conditions

```python
test.run()
```

Once the test sequence is finished we can get the results as an *xarray Dataset*.

```python
test.ds_results
```

Can also get individual results from a _Measurement_ object directly.

```python
test.meas.MeasureVolume.ds_results
```

Individual measurements can be run with specific conditions independent of the _TestManager_.

```python
conditions = dict(temperature_degC=34,pressure_nm=15)
test.meas.MeasureVolume.run(conditions)
```

Or measurements can be run without specifiying conditions

```python
test.meas.MeasureVolume.run()
```

Note in the last two cases where the measurement is run individually, specifiying the conditions merely includes the conditions as coordinates in the results Dataset. _Measurement_ classes _do not_ set their own conditions, that is only done by _SetupConditions_ classes.

## Creating a measurement sequence

A measurement sequence consists of a _TestManager_ class to run the overall sequence, any number of _SetupConditions_ classes and any number of _Measurement_ classes.

Let's take a simple example, the measurement of resistance of a resistor.

```
+--------------+
|   voltage    |
|   source     +-----+
|              |     |
+--------------+     |
                     |
                     |
                   +-+-+
                   |   |
                   |   |
                   | R |    Resistor to measure
                   |   |
                   |   |
                   |   |
                   +-+-+
                     |
                     |
                +----+-----+
                |          |
                | Ammeter  |
                |          |
                +----+-----+
                     |
                     |
                 --------- Ground
                   -----
                    ---

```
We have two pieces of test equipment in this measurement: the voltage source and the ammeter. The measurement is simply to set a voltage, measure the current, and calculate the resistance from Ohm's law :

Voltage = Resistance x Current

In this measurement we have one setup condition, voltage, one measurement, current and one processing step, resistance.

Let's assume that the voltage source and ammeter are controlled through the objects *voltage_source* and *ammeter*. These two objects will be supplied as _resources_ to the _TestManager_, _SetupConditions_ and _Measurement_ classes e.g.

```python
resources = {'voltage_source':voltage_source, 'ammeter':ammeter}
```
All classes will automatically have the *voltage_source* and *ammeter* objects available as properties.

### Setup conditions

First we'll setup the voltage source. This is our only setup condition and it will be done using a _SetupConditions_ class. _SetupConditions_ classes inherit from the abstract class _AbstractSetupConditions_. They require one method and two properties to be defined:

* _initialise_ : Perform any initialisation, usually setting defaults for the property _values_.
* _setpoint_ : Property that is used to set/get the condition set point value
* _actual_ : Property that returns the actual value of the condition, e.g. the actual voltage rather than the setpoint

The complete class definition is shown here:

```python
class Voltage(tmpl.AbstractSetupConditions):

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [3.0]

        
    @property
    def actual(self):
        """
        Return actual measured voltage
        """
        return self.voltage_source.actual_voltage_V

    @property
    def setpoint(self):
        """
        Get/Set the output voltage of the voltage source
        """
        return self.voltage_source.voltage_set_V

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Set Voltage source to {value}V') # printout
        self.voltage_source.voltage_set_V = value
        
```

### Measurements

Next the central measurement class is defined. Measurement classes inherit from the _AbstractMeasurement_ class. The only method that _needs_ to be defined is *meas_sequence()*. This is generally the top level function of a specific measurement procedure. Any number of extra methods can be added to the class to support *meas_sequence()*, but when a measurement is executed it basically calls the *meas_sequence()* method.

In this case the measurement is simply to read the ammeter and store the reading, which can be done in the *meas_sequence()*. The resistance, however, is derived from the ammeter reading and the setpoint of the voltage source. Since this is "processing" rather than measurement it is good practice to do this in another method. This ensures that the real measurement, the ammeter reading, is done even if the processing step crashes. In this case the processing function could be re-run later to debug it, without re-running the measurement.

```python
class CurrentMeasure(tmpl.AbstractMeasurement):
           

    def meas_sequence(self):
        """
        Mandatory method for Measurement classes

        Performs the actual measurement and stores data.
        """
        #  Measure current with ammeter
        current = self.ammeter.current_A

        # Store the data
        self.store_data_var('current_A',current)

        # Process
        self.process_results()


    @tmpl.with_results(data_vars=['current_A'])
    def process_results(self):
        """
        Calculate resistance using measured current and voltage source
        setting.
        """

        # Get voltage from current conditions
        Voltage = self.current_conditions['Voltage']

        # Get current measured at the last conditions
        current_A = self.current_results.current_A
        resistance_ohms = Voltage/current_A

        self.store_data_var('resistance_ohms',[resistance_ohms])
```
The *process_results()* method uses the *tmpl.with_results* [decorator](https://wiki.python.org/moin/PythonDecorators#What_is_a_Decorator) to ensure that there is always an entry stored called *current_A*. If *process_results()* were to be executed before *meas_sequence()* then an error would be thrown because *current_A* had not been created. The *tmpl.with_results* decorator is not mandatory it is a convenience that avoids having to add boilerplate code such as :

```python
assert 'current_A' in self.ds_results
# use decorator instead: @tmpl.with_results(data_vars=['current_A'])
```
Note also that *tmpl.with_results()* can have a list of names passed to it if more than one value has been measured and stored.


### Test manager

Now that the setup conditions and measurement have been defined, all that remains is to assemble the top level test sequence class. Again this is inherited from an abstract class: *AbstractTestManager*

```python
class SimpleResistanceMeasurement(tmpl.AbstractTestManager):

    def define_setup_conditions(self):
        """
        Add the setup conditions here in the order that they should be set
        """

        # Add setup conditions using class name
        self.add_setup_condition(Voltage)
        

    def define_measurements(self):
        """
        Add measurements here in the order of execution
        """

        # Setup links to all the measurements using class name
        self.add_measurement(CurrentMeasure)
        
```

The test manager requires two methods to be defined:

* *define_setup_conditions()* : This method is a list of calls to *self.add_setup_condition(\<class name>)*. This method takes the name of the SetupConditions class defined previously. In this case there is only one setup condition, Voltage, but if there are multiple SetupConditions classes they are all added here *in the order that they should be set*.
* *define_measurements()* : Similarly measurement classes are added using their class names using the *self.add_measurement(\<class name>)*. Again the order here dictates the order in which the measurements will be executed.

### Running the test

With the classes defined the test can be run by supplying the required resources to the test manager class:

```python
import tmpl

# Make the instrument objects
R = tmpl.examples.ResistorModel(10e3)
vs = tmpl.examples.VoltageSupply(R)
am = tmpl.examples.Ammeter(R)

# Make resources
resources = {'voltage_source':vs, 'ammeter':am}

# Create test manager
test = SimpleResistanceMeasurement(resources)

# Run the test
test.run()
```
the output should look like this:

```
@ SimpleResistanceMeasurement | Generating the sequence running order
@ SimpleResistanceMeasurement | 	Running order done
@ SimpleResistanceMeasurement | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ SimpleResistanceMeasurement | Running SimpleResistanceMeasurement
@ SimpleResistanceMeasurement | Generating the sequence running order
@ SimpleResistanceMeasurement | 	Running order done
------------------------------------------------------------
@ Voltage                   | Set Voltage source to 3.0V
@ CurrentMeasure            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ CurrentMeasure            | Running CurrentMeasure
@ CurrentMeasure            | CurrentMeasure	Time taken: 0.003s 
@ CurrentMeasure            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@ SimpleResistanceMeasurement | ========================================
@ SimpleResistanceMeasurement | SimpleResistanceMeasurement	Time taken: 0.006s 
@ SimpleResistanceMeasurement | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
```

### Running order

Internally TMPL generates a list of functions to call when the *run()* method is called. It can be useful to view this running order before actually running the test sequence. The property *df_running_order* displays this in a [pandas](https://pandas.pydata.org/pandas-docs/stable/) DataFrame for a convenient tabular printout.

Here's the running order of the resistance measurement example:

```python
>>> test.df_running_order

     Operation           Label  Voltage
0    CONDITION         Voltage      3.0
1  MEASUREMENT  CurrentMeasure      3.0
```
It shows that the test sequence consists of two steps, the first step is a *CONDITION* operation, i.e. setting the voltage. The second step is a *MEASUREMENT*, i.e. reading the Ammeter.

### Results data

The whole point of the TMPL library is to get experimental data into [xarray](http://xarray.pydata.org/en/stable/) Dataset format. Once a test sequence has been run, all the data collected will be available from the test manager object in the property *ds_results*. *ds_results* is an xarray Dataset object. Here's the result of the simple resistance measurement:

```python
>>> test.ds_results # Display results from test sequence

<xarray.Dataset>
Dimensions:          (Voltage: 1)
Coordinates:
  * Voltage          (Voltage) float64 3.0
Data variables:
    current_A        (Voltage) float64 0.0002963
    resistance_ohms  (Voltage) float64 1.013e+04

```

The data can be stored and re-loaded in JSON format

```python
# Save to JSON
test.save('my_data.json')

# Load from JSON
test.load('my_data.json')

```
This stores the *ds_results* Dataset into JSON format, which can be loaded back in later. Loading previously measured data can be useful for testing new processing functions.

#### Individual Measurement data

The *ds_results* property of a test manager class, e.g. *test*, scoops up all the data measured in individual measurement class object and puts it into one Dataset. However the individual measurement data can be accessed in the same way. All TMPL class objects have a *ds_results* property and all can be saved and loaded in the same way.

So for the resistor measurement example we can access the data from the measurement class, *CurrentMeasure* like this:

```python
>>> test.meas.CurrentMeasure.ds_results

<xarray.Dataset>
Dimensions:          (Voltage: 1)
Coordinates:
  * Voltage          (Voltage) float64 3.0
Data variables:
    current_A        (Voltage) float64 0.0002963
    resistance_ohms  (Voltage) float64 1.013e+04
```
It looks exactly the same as *test.ds_results*, because *CurrentMeasure* is the only measurement class in this test sequence. It can also be saved and loaded in the same manner.

```python
# Save to JSON
test.meas.CurrentMeasure.save('my_data.json')

# Load from JSON
test.meas.CurrentMeasure.load('my_data.json')

```

### Dataset extra features

TMPL adds some extra features to Datasets for easy storing of the data. It registers a [dataset_accessor](http://xarray.pydata.org/en/stable/internals/extending-xarray.html), which adds the *save* property to the Dataset. The *save* property has several functions for saving the Dataset into different formats as shown here:

```python
# Save Dataset to JSON
test.ds_results.save.to_json(filename)

# Save Dataset to JSON string
jstr = test.ds_results.save.to_json_str()

# Save Dataset to Excel spreadsheet
test.ds_results.save.to_excel(filename)

```

