"""
Module: repeated_measurements
================================================================
<Description of module>

SetupCondition classes:
* Year :
* Month :

Measurement classes:
* GetSeconds :
* GetHour :
* GetDay :

TestManager classes:
* MainMeasure :



This module is based on the "Test, Measure, Process Library" (TMPL)
framework for organising measurement code.
See: https://pypi.org/project/test-measure-process-lib/

"""

#================================================================
#%% Imports
#================================================================
# Standard library
import os
import time
import datetime
import random

# Third party libraries
import numpy as np
import pandas as pd
import tmpl

#================================================================
#%% SetupCondition classes
#================================================================

class Year(tmpl.AbstractSetupConditions):
    """
    <Description of condition>
    """
    #name = '<name_in_dataset' # Name used in ds_results dataset (optional)

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [1984]
        self.current_year = 1900


    @property
    def actual(self):
        return self.current_year 

    @property
    def setpoint(self):
        return self.current_year

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} ')
        self.current_year = value
        return value



class Month(tmpl.AbstractSetupConditions):
    """
    <Description of condition>
    """
    #name = '<name_in_dataset' # Name used in ds_results dataset (optional)

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [8]
        self.current_month = 7


    @property
    def actual(self):
        return self.current_month

    @property
    def setpoint(self):
        return self.current_month

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} ')
        self.current_month = value
        return value



#================================================================
#%% Measurement classes
#================================================================

class GetSeconds(tmpl.AbstractMeasurement):
    """
    <Description of measurement>

    """

    def initialise(self):
        # Run conditions (optional)
        # self.run_on_startup(True)
        # self.run_on_teardown(True)
        # self.run_on_error(True)
        # self.run_on_setup(condition_label,value=None)
        # self.run_after(condition_label,value=None)

        # Set up configuration values
        self.config.offset = 0.1
        

    def meas_sequence(self):
        """
        <More description (optional)>
        """
        
        dt = datetime.datetime.now()
        rnd = random.randint(0,10)/100
        sec = dt.second + self.config.offset + rnd
        self.log(f'Seconds = {sec}')
        self.store_data_var('second',sec)
        


class GetHour(tmpl.AbstractMeasurement):
    """
    <Description of measurement>

    """

    def initialise(self):
        # Run conditions (optional)
        # self.run_on_startup(True)
        # self.run_on_teardown(True)
        # self.run_on_error(True)
        # self.run_on_setup(condition_label,value=None)
        # self.run_after(condition_label,value=None)

        # Set up configuration values
        self.config.offset = 0.2
        

    def meas_sequence(self):
        """
        <More description (optional)>
        """
        dt = datetime.datetime.now()
        self.log(f'Hour = {dt.hour}')
        self.store_data_var('hour',dt.hour+ self.config.offset)
        
        


class GetDay(tmpl.AbstractMeasurement):
    """
    <Description of measurement>

    """

    def initialise(self):
        # Run conditions (optional)
        # self.run_on_startup(True)
        # self.run_on_teardown(True)
        # self.run_on_error(True)
        # self.run_on_setup(condition_label,value=None)
        # self.run_after(condition_label,value=None)

        # Set up configuration values
        self.config.offset = 0.3
        

    def meas_sequence(self):
        """
        <More description (optional)>
        """
        dt = datetime.datetime.now()
        self.log(f'Day = {dt.day}')
        self.store_data_var('day',dt.day + self.config.offset)
        
        


#================================================================
#%% TestManager classes
#================================================================

class MainMeasure(tmpl.AbstractTestManager):
    """
    <Description of test sequence>
    """

    def define_setup_conditions(self):
        """
        Add the setup conditions here in the order that they should be set
        """
        self.add_setup_condition(Year)
        self.add_setup_condition(Month)


    def define_measurements(self):
        """
        Add measurements here in the order of execution
        """

        # Setup links to all the measurements
        self.add_measurement(GetSeconds)
        self.add_measurement(GetHour)
        self.add_measurement(GetDay)
        self.add_measurement(GetSeconds,meas_name='Sec2')


    def initialise(self):
        """
        Add custom information here
        """
        
        self.information.serial_number = 'example_sn'
        self.information.part_number = 'example_pn'
        # Add more here ...
 
class MainMeasure_fail(MainMeasure):
    """
    Version of MainMeasure that does not use meas_name to add repeated measurements
    """

    def define_measurements(self):
        """
        Add measurements here in the order of execution
        """

        # Setup links to all the measurements
        self.add_measurement(GetSeconds)
        self.add_measurement(GetHour)
        self.add_measurement(GetDay)
        self.add_measurement(GetSeconds) # This should display a warning
