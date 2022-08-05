
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
        # self.add_setup_condition(Humidity)

    def define_measurements(self):
        """
        Add measurements here in the order of execution
        """

        # Setup links to all the measurements using class name
        # self.add_measurement(Voltage)
        self.add_measurement(Current)
        # self.add_measurement(Resistance)
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run something
    print('Run')

    R = tmpl.examples.ResistorModel(10e3)
    vs = tmpl.examples.VoltageSupply(R)
    am = tmpl.examples.Ammeter(R)
    ch = tmpl.examples.EnvironmentalChamber(R)

    resources = { 'ammeter':am,'chamber':ch}

    test = ResistanceMeasureSequence(resources)

    test.df_running_order

    test.run()