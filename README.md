# Test, Measure, Process library (TMPL)

This library is a modular framework for running sequences of measurements. It is intended to provide a minimal boiler-plate code framework for writing measurement code in modules that can be linked together into test sequences. Although written for use in measurements the framework makes no assumptions about test equipment setup and is very generic. It could be used to make test sequences based on models or data analysis instead of actual measurements.

The framework is built around storing data in the [xarray](http://xarray.pydata.org/en/stable/) _Dataset_ class. This provides a convenient data structure for storing multi-dimensional data that can be easily visualised using libraries like [Holoviews](http://holoviews.org/index.html) or its offshoot [hvplot](https://hvplot.holoviz.org/index.html).

## Core classes

The framework is built on a set of core classes. These are built by inheriting from the Abstract classes defined in *tmpl_core.py*. The classes are:

* _TestManager_ classes: Based on _AbstractTestManager_ class. These classes run sequences of measurements over multiple setup conditions e.g. temperature, humidity etc. The _TestManagers_ are ultimately responsible for gathering up all data recorded during the sequence and packaging it into one xarray Dataset object.
* _Measurement_ classes: Based on _AbstractMeasurement_ class. These are the classes that actually perform the measurements. They are classes that can be run independently or in a sequence from a _TestManager_. The data that they collect and process is stored in an internal xarray Dataset object. When run from a _TestManager_ this dataset will be scooped up at the end of the sequence and added into the overall Dataset maintained by the _TestManager_.
* _SetupCondition_ classes: Based on _AbstractSetupCondition_. These classes are responsible for setting up experimental conditions e.g. temperature, wavelength, supply voltage etc. They are small classes that have only one purpose, to set a specific condition. _TestManagers_ use _SetupCondition_ classes to set conditions during a sequence before running measurements. 


## Example usage

Before explaining the inner workings of the framework this section runs through a hypothetical example to show how the classes are used at the top level.

Suppose a _TestManager_ has been defined that has objects for setting *temperature and wavelength*. It also has three measurement objects defined called *dark_currents, InnerSweep and OuterSweep*.

The _TestManager_ is initialised with any _resources_ that the measurement classes require, e.g. instruments.

```python
# Define test equipment objects for measurements to use
# - can be anything that Measurement classes require
resources = {'station':station_object,
            'dut':dut_object,'instrument':instr_object}

# Create test manager object
test = TestManager_mymeas(resources)
```

Setup conditions under which test is to be run can be defined by accessing the _SetupConditions_ objects directly through the _setup_ property.

```python
test.setup.temperature.values = [25,40,75]
test.setup.wavelength.values = [1528,1545,1565]
```

The measurements to run during the sequence can be enabled/disabled by direct access to the _Measurement_ objects through the _meas_ property.

```python
test.meas.dark_currents.enable = False
test.meas.InnerSweep.enable = True
test.meas.OuterSweep.enable = True
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
test.meas.InnerSweep.ds_results
```

Individual measurements can be run with specific conditions independent of the _TestManager_.

```python
conditions = dict(temperature_degC=34,wavelength_nm=1550)
test.meas.InnerSweep.run(conditions)
```

Or measurements can be run without specifiying conditions

```python
test.meas.InnerSweep.run()
```

Note in the last two cases where the measurement is run individually, specifiying the conditions merely includes the conditions as coordinates in the results Dataset. _Measurement_ classes _do not_ set their own conditions, that is only done by _SetupConditions_ classes.