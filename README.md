# Test, Measure, Process library (TMPL)

This library is a modular framework for running sequences of lab measurements. It is intended to provide a minimal boiler-plate code framework for writing measurement code in modules that can be linked together into test sequences. Although written for use in lab measurements the framework makes no assumptions about test equipment setup and is very generic. It could be used to make test sequences based on models or data analysis instead of actual measurements.

The framework is built around storing data in the [xarray](http://xarray.pydata.org/en/stable/) _Dataset_ class. This provides a convenient data structure for storing multi-dimensional data that can be easily visualised using libraries like [Holoviews](http://holoviews.org/index.html) or its offshoot [hvplot](https://hvplot.holoviz.org/index.html).

## Dependencies and installation
TMPL depends on these libraries. 

* [xarray](http://xarray.pydata.org/en/stable/)
* [pandas](https://pandas.pydata.org/pandas-docs/stable/)
* [xlsxwriter](https://xlsxwriter.readthedocs.io/)

TMPL can be installed via *pip*

```bash
pip install test-measure-process-lib
```

Note that this does not install the dependencies. This is in case another package manager, e.g. Anaconda, is being used. So they have to be manually installed.

## Documentation
This file gives basic descriptions of how to use TMPL, for more details consult [the full documentation](https://redlegjed.github.io/test_measure_process_lib/)


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

Setup conditions under which test is to be run can be defined by accessing the _SetupConditions_ objects directly through the _conditions_ property.

```python
test.conditions.temperature.values = [25,40,75]
test.conditions.pressure.values = [12,15,65]
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



    @tmpl.with_results(data_vars=['current_A'])
    def process(self):
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
The *process()* method is called automatically after the *meas_setup()* method if it is present.

The *process()* method uses the *tmpl.with_results* [decorator](https://wiki.python.org/moin/PythonDecorators#What_is_a_Decorator) to ensure that there is always an entry stored called *current_A*. If *process_results()* were to be executed before *meas_sequence()* then an error would be thrown because *current_A* had not been created. The *tmpl.with_results* decorator is not mandatory it is a convenience that avoids having to add boilerplate code such as :

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

The whole point of the TMPL library is to get experimental data into [xarray](http://xarray.pydata.org/en/stable/) Dataset format. Once a test sequence has been run, all the data collected will be available from the test manager object in the property *ds_results*. *ds_results* is an [xarray Dataset](http://xarray.pydata.org/en/stable/user-guide/data-structures.html#dataset) object. Here's the result of the simple resistance measurement:

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

## More advanced example

The simple resistance measurement was good for demonstrating the basic operation of TMPL. Now we will look at a more advanced example. It is still based on measuring the resistance of a resistor but this time we will make the measurement more sophisticated in the following ways.

* Instead of using the setting of the voltage source for the voltage value, we will use a dedicated voltmeter across the resistor.
* Rather than calculating resistance from single values of voltage and resistance we will sweep the voltage and measure the current. We can then fit a line to these measurements and obtain resistance from the slope of the line.
* We also want to measure the resistance variation against environmental conditions so we will put it in a chamber that can vary the temperature and humidity.

Here's a diagram of the new setup:
```
+--------------+
|   voltage    |
|   source     +-----+
|              |     |
+--------------+     |
                     +----------------------+
                     |                      |
           +---------------+         +------+------+
           |         |     |         |             |
 Chamber   |       +-+-+   |         |             |
           |       |   |   |         |             |
    +------+       | R |   |         | Voltmeter   |
    | Temp |       |   |   |         |             |
    +------+       |   |   |         |             |
    | Hum  |       +-+-+   |         +-------+-----+
    +------+         |     |                 |
           +---------------+                 |
                     |                       |
                     +-----------------------+
                     |
                +----+-----+
                | Ammeter  |
                |          |
                +----+-----+
                     |
                     |
                 +-------+ Ground
                   +---+
                    +-+

```

Now our representation in TMPL will be:

* Setup condition:
  - Temperature
  - Humidity
  - Voltage source setpoint
* Measurements:
  - Current (from Ammeter)
  - Voltage across resistor (from Voltmeter)

First we'll need more resources for the new equipment: an environmental chamber for setting temperature and humidity, plus a voltmeter.


```python
resources = {'chamber':chamber_object,
            'voltage_source':voltage_source_object, 
            'ammeter':ammeter_object,
            'voltmeter':voltmeter_object}
```
These will be given to the test manager class.

### Setup conditions

We now need some new setup condition classes for temperature and humidity. These will make use of the chamber *temperature_degC* and *humidity_pc* properties like this:

```python
class Temperature(tmpl.AbstractSetupConditions):

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [25,35,45]

    @property
    def actual(self):
        return self.chamber.temperature_degC

    @property
    def setpoint(self):
        return self.chamber.temperature_setpoint_degC

    @setpoint.setter
    def setpoint(self,value):
        self.chamber.temperature_setpoint_degC = value


class Humidity(tmpl.AbstractSetupConditions):

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [55,85]

    @property
    def actual(self):
        return self.chamber.humidity_degC

    @property
    def setpoint(self):
        return self.chamber.humidity_setpoint_degC

    @setpoint.setter
    def setpoint(self,value):
        self.chamber.humidity_setpoint_degC = value


```

This time we are not going to use the voltage source as a setup condition because we want to sweep the voltage.

### Measurements

The main measurement in this example will be a sweep of the voltage source setpoint. During this sweep the current from the ammeter and the voltage from the voltmeter will be measured. This requires a new measurement class to be created.

```python

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


    @tmpl.with_results(data_vars=['current_A','voltage_diff_V'])
    def process(self):

        volts = self.current_results.voltage_diff_V.values
        amps = self.current_results.current_A.values

        # Fit line to amps vs volts, get resistance from slope
        fit_coefficients=np.polyfit(amps,volts,1)
        resistance_ohms = fit_coefficients[0] # slope

        self.store_data_var('resistance_ohms',[resistance_ohms])

```
This measurement is more detailed than the previous example. Measurement classes can have an _initialise()_ method where configuration parameters can be defined. In this case we are defining the voltage values that going to be swept over in the line:

```python
self.config.voltage_sweep = np.linspace(0,1,10)
```
Every TMPL class has a _config_ dictionary that can be used to store any kind of data. It is a special dictionary defined in TMPL called an _ObjDict_, where elements can be added by using the dot notation to assign values. The standard _dict_ way can also be used. We could equally have used:

```python
self.config['voltage_sweep'] = np.linspace(0,1,10)
```
Measurements are just normal classes so you can define your own properties as well. Using the _config_ dict just organises the data under one roof.

The mandatory *meas_setup()* is now a loop that follows the sequence:
* Set voltage
* Measure current
* Measure voltage across resistor

Where the two measurements are stored in 1 dimensional arrays.

The last part of the *meas_setup()* method stores the data. The current and measured voltage are functions of the *voltage_sweep* values. To capture this relationship we need to make *voltage_sweep* into a coordinate in addition to the setup conditions of temperature and humidity. This is done by explicitly storing *voltage_sweep* as a coordinate and indicating in *store_data_vars()* that it is a coordinate.

```python
# Store the data
self.store_coords('swp_voltage',self.config.voltage_sweep)
self.store_data_var('current_A',current,coords=['swp_voltage'])
self.store_data_var('voltage_diff_V',voltage,coords=['swp_voltage'])
```
In order to do this the data being stored must be the same shaped array as the coordinate. In this case everything is a 1D array.

The *process()* method operates just as before. It requires that the current and voltage have been measured. If they have then it will fit a line to the data and get the resistance from the slope of that line.

### Test manager

Now we can assemble the setup condition and measurement into a *TestManager* class. This follows the same pattern as before:

```python
class AdvancedResistanceMeasurement(tmpl.AbstractTestManager):

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
        self.add_measurement(VoltageSweeper)
```

Set up the *TestManager* object:

```python
import tmpl

# Setup resources
R = tmpl.examples.ResistorModel(10e3)
vs = tmpl.examples.VoltageSupply(R)
am = tmpl.examples.Ammeter(R)
vm = tmpl.examples.Voltmeter(R)
chamber = tmpl.examples.EnvironmentalChamber(R)
resources = {'voltage_source':vs, 'ammeter':am,'voltmeter':vm,'chamber':chamber}

# Create test manager 
test = AdvancedResistanceMeasurement(resources)
```


We can see the running order again:
```python
>>> test.df_running_order
@ AdvancedResistanceMeasurement | Generating the sequence running order
@ AdvancedResistanceMeasurement | 	Running order done
      Operation           Label  Temperature  Humidity
0     CONDITION     Temperature         25.0       NaN
1     CONDITION        Humidity          NaN      55.0
2   MEASUREMENT  VoltageSweeper         25.0      55.0
3     CONDITION        Humidity          NaN      85.0
4   MEASUREMENT  VoltageSweeper         25.0      85.0
5     CONDITION     Temperature         35.0       NaN
6     CONDITION        Humidity          NaN      55.0
7   MEASUREMENT  VoltageSweeper         35.0      55.0
8     CONDITION        Humidity          NaN      85.0
9   MEASUREMENT  VoltageSweeper         35.0      85.0
10    CONDITION     Temperature         45.0       NaN
11    CONDITION        Humidity          NaN      55.0
12  MEASUREMENT  VoltageSweeper         45.0      55.0
13    CONDITION        Humidity          NaN      85.0
14  MEASUREMENT  VoltageSweeper         45.0      85.0
```

and run the test:

```python
>>> test.run()
Run
@ AdvancedResistanceMeasurement | Generating the sequence running order
@ AdvancedResistanceMeasurement | 	Running order done
@ AdvancedResistanceMeasurement | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ AdvancedResistanceMeasurement | Running AdvancedResistanceMeasurement
@ AdvancedResistanceMeasurement | Generating the sequence running order
@ AdvancedResistanceMeasurement | 	Running order done
------------------------------------------------------------
------------------------------------------------------------
@ VoltageSweeper            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ VoltageSweeper            | Running VoltageSweeper
@ VoltageSweeper            | finished sweep
@ VoltageSweeper            | VoltageSweeper	Time taken: 0.008 s 
@ VoltageSweeper            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
------------------------------------------------------------
@ VoltageSweeper            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ VoltageSweeper            | Running VoltageSweeper
@ VoltageSweeper            | finished sweep
@ VoltageSweeper            | VoltageSweeper	Time taken: 0.008 s 
@ VoltageSweeper            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
------------------------------------------------------------
------------------------------------------------------------
@ VoltageSweeper            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ VoltageSweeper            | Running VoltageSweeper
@ VoltageSweeper            | finished sweep
@ VoltageSweeper            | VoltageSweeper	Time taken: 0.007 s 
@ VoltageSweeper            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
------------------------------------------------------------
@ VoltageSweeper            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ VoltageSweeper            | Running VoltageSweeper
@ VoltageSweeper            | finished sweep
@ VoltageSweeper            | VoltageSweeper	Time taken: 0.008 s 
@ VoltageSweeper            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
------------------------------------------------------------
------------------------------------------------------------
@ VoltageSweeper            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ VoltageSweeper            | Running VoltageSweeper
@ VoltageSweeper            | finished sweep
@ VoltageSweeper            | VoltageSweeper	Time taken: 0.008 s 
@ VoltageSweeper            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
------------------------------------------------------------
@ VoltageSweeper            | <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
@ VoltageSweeper            | Running VoltageSweeper
@ VoltageSweeper            | finished sweep
@ VoltageSweeper            | VoltageSweeper	Time taken: 0.007 s 
@ VoltageSweeper            | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@ AdvancedResistanceMeasurement | ========================================
@ AdvancedResistanceMeasurement | AdvancedResistanceMeasurement	Time taken: 0.049 s 
@ AdvancedResistanceMeasurement | >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

```

## Installing for development

TMPL can be installed locally by cloning the repository to a local folder and then installing with pip

```bash
cd <local_path>
git clone https://github.com/redlegjed/test_measure_process_lib.git
pip install -e <local_path>/test_measure_process_lib

```

The code can then be edited from *<local_path>/test_measure_process_lib*. Changes will be included when importing *tmpl* into a new python instance.