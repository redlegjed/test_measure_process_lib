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
#%% Classes
#================================================================
class Voltage(tmpl.AbstractSetupConditions):
    # name = 'Voltage'

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
        self.log(f'Set Voltage source to {value}V')
        self.voltage_source.voltage_set_V = value
        

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
 
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run something
    print('Run')

    R = tmpl.examples.ResistorModel(10e3)
    vs = tmpl.examples.VoltageSupply(R)
    am = tmpl.examples.Ammeter(R)
    resources = {'voltage_source':vs, 'ammeter':am}

    test = SimpleResistanceMeasurement(resources)

    test.df_running_order

    test.run()