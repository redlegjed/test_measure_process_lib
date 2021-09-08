'''
Simple Resistor test from README
================================================================
Example used in README.md
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

import tmpl
 
#================================================================
#%% Constants
#================================================================
 
#================================================================
#%% Functions
#================================================================

 
#================================================================
#%% Conditions classes
#================================================================
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
#================================================================
#%% Measurement classes
#================================================================

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


    @tmpl.with_results(data_vars=['current_A','voltage_diff_V'])
    def process(self):

        volts = self.current_results.voltage_diff_V.values
        amps = self.current_results.current_A.values

        # Fit line to amps vs volts, get resistance from slope
        fit_coefficients=np.polyfit(amps,volts,1)
        resistance_ohms = fit_coefficients[0] # slope

        self.store_data_var('resistance_ohms',[resistance_ohms])


class PostProcess(tmpl.AbstractMeasurement):
    """
    Post processing class - executed at the end

    """

    def initialise(self):
        self.run_on_teardown(True)

    def meas_sequence(self):
        pass
    
    def process(self):
        
        # Pull all results data to check it's there
        ds = self.ds_results_global
        print(ds)

        # TODO Process data


#================================================================
#%% Test Manager class
#================================================================
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
        self.add_measurement(PostProcess)
 
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run something
    print('Run')

    R = tmpl.examples.ResistorModel(10e3)
    vs = tmpl.examples.VoltageSupply(R)
    am = tmpl.examples.Ammeter(R)
    vm = tmpl.examples.Voltmeter(R)
    chamber = tmpl.examples.EnvironmentalChamber(R)
    resources = {'voltage_source':vs, 'ammeter':am,'voltmeter':vm,'chamber':chamber}

    test = AdvancedResistanceMeasurement(resources)

    test.df_running_order

    test.run()