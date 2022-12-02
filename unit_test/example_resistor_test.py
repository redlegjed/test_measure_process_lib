'''
Example Resistor test
================================================================
This is a simple example of using the TMPL framework to measure a
resistor.
The resistor will be measured under different conditions of temperature
and humidity. Also different types of resistor will be measured.

As this is an example there is no actual hardware. The resistors
and measurement instruments are simulated by simple functions.

'''
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os, time
#from collections import OrderedDict
 
# Third party libraries
import numpy as np
import pandas as pd

# Local libraries
import tmpl
 
#================================================================
#%% Resistor model
#================================================================
# Define a simple class for a resistor that allows the experimental
# conditions to be setup and for the voltage across the resistor to 
# be set.
class ResistorModel():
    """
    Simple resistor model.
    """
    def __init__(self,resistance_ohms,tolerance_pc=1.0) -> None:
        
        # Basics
        # ------------
        self.resistance_base_ohms = resistance_ohms
        self.tolerance_pc = tolerance_pc

        # Environmental conditions
        # ------------------------------
        # These are set by external functions

        self.voltage = 0.0
        self.temperature_degC = 25.0
        self.humidity_pc = 40.0

        # Define some relations to temperature and humidity
        # - purely to generate different values according to these conditions
        self.temperature_factor = 1
        self.humidity_factor = 1/100

        

    @property
    def resistance_ohms(self):
        """
        Return resistance at current conditions
        """
        # Base resistance value
        R_ohms = self.resistance_base_ohms*(1 + self.tolerance_pc/100)

        # Additional resistance due to temperature and humidity
        R_T_ohms = self.temperature_degC*self.temperature_factor
        R_H_ohms = self.humidity_pc*self.humidity_factor

        return R_ohms + R_T_ohms + R_H_ohms


    @property
    def current_A(self):
        """
        Return current through resistor at current conditions
        """
        return self.voltage/self.resistance_ohms
 
#================================================================
#%% Measurement Functions/classes
#================================================================
# These functions and classes are the 'resources' required by
# the test class instances
# They are standing in for real instruments.
# They all make use of the ResistorModel as an input

def set_temperature(resistor,temperature_degC):
    resistor.temperature_degC = temperature_degC

def set_humidity(resistor,humidity_pc):
    resistor.humidity_pc = humidity_pc


class VoltageSupply():
    """
    Example of using a class that represents and instrument
    """

    def __init__(self) -> None:
        pass

    def set_voltage(self,voltage,resistor):
        resistor.voltage = voltage
 
#================================================================
#%% Setup conditions classes
#================================================================
# Classes that define setup conditions. These have a standard format
# that is defined by the AbstractSetupConditions class

class TemperatureConditions(tmpl.AbstractSetupConditions):
    """
    Temperature setpoint condition

    """
    name = 'temperature_degC'

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [25,35,45]

        # Setpoint
        self._setpoint = 25

    @property
    def actual(self):
        return self.resistor.temperature_degC

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} degC')
        self._setpoint = value
        # Use set_temperature, which is automatically available
        # from resources
        return self.set_temperature(self.resistor,value)



class HumidityConditions(tmpl.AbstractSetupConditions):
    """
    Humidity setpoint condition

    """
    name = 'humidity_pc'

    def initialise(self):
        """
        Initialise default values and any other setup
        """
        # Set default values
        self.values = [55,60,70]

        # Setpoint
        self._setpoint = 45

    @property
    def actual(self):
        return self.resistor.humidity_pc

    @property
    def setpoint(self):
        return self._setpoint

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} %')
        self._setpoint = value
        # Use set_humidity, which is automatically available
        # from resources
        return self.set_humidity(self.resistor,value)

#================================================================
#%% Measurement classes
#================================================================
#  Measurement class that runs at every combination of setup conditions
# Has a standard format defined by AbstractMeasurement

class VoltageSweeper(tmpl.AbstractMeasurement):
    """
    Example of a Measurement that adds its own coordinates and has
    a process method

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

        p=self.current_results.current_A.polyfit('swp_voltage',1)
        resistance_ohms = p.polyfit_coefficients.sel(degree=1).values

        self.store_data_var('resistance_ohms',[resistance_ohms])

# Measurement class that runs every time the temperature changes
class Stabilise(tmpl.AbstractMeasurement):
    """
    Wait for stabilisation

    """

    def initialise(self):
        self.run_on_setup('temperature_degC')

    def meas_sequence(self):
        self.log('Stabilising')


# Measurement classes that run at start and end of test sequence
class TurnOn(tmpl.AbstractMeasurement):
    """
    Turn on all equipment

    """

    def initialise(self):
        self.run_on_startup(True)


    def meas_sequence(self):
        self.log('TurnOn measurement')


class TurnOff(tmpl.AbstractMeasurement):
    """
    Turn off all equipment

    """

    def initialise(self):
        self.run_on_teardown(True)


    def meas_sequence(self):
        self.log('TurnOff measurement')
#================================================================
#%% Test Manager class
#================================================================
# The top level sequence is responsible for running the complete measurement
# It sets every combination of setup conditions and runs measurements at each

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
        self.add_measurement(TurnOn)
        self.add_measurement(Stabilise)
        self.add_measurement(VoltageSweeper)
        self.add_measurement(TurnOff)


    def initialise(self):
        """
        Add custom information here
        """
        
        self.information.serial_number = 'example_sn'
        self.information.part_number = 'example_pn'
 
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run a full test sequence

    # Define resistor model
    res1 = ResistorModel(100,tolerance_pc=1.0)

    # Setup resources
    resources = {
        'set_temperature':set_temperature,
        'set_humidity': set_humidity,
        'voltage_supply':VoltageSupply(),
        'resistor':res1,
        }

    config_custom = {'param1':1,'param2':2}

    # Create and run the test sequence
    test = ExampleTestSequence(resources,config=config_custom)
    test.run()