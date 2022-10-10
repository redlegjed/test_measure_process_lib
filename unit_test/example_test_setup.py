'''
Example of test class setup using test_measure_process library
================================================================
Define a full set of classes using the TMPL library

These classes use station & testboard classes to perform measurements.

* Tests services

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
#%% Resource classes
#================================================================
# Dummy station and testboard classes

class ExampleStation():

    def __init__(self) -> None:
        
        self._temperature = 25
        self._humidity = 25

    def set_temperature_setpoint(self,value):
        self._temperature = value

    def get_temperature_setpoint(self):
        return self._temperature 

    def get_temperature(self):
        return self._temperature + 0.01*np.random.rand()


    def set_humidity_setpoint(self,value):
        self._humidity = value

    def get_humidity_setpoint(self):
        return self._humidity 

    def get_humidity(self):
        return self._humidity + 0.01*np.random.rand()


class ExampleTestboard():

    def sweep(self,label):
        """
        generate some sweep x,y data given a label

        Parameters
        ----------
        label : str
            [description]

        Returns
        -------
        dict
            with keys 'x' & 'y' for the data

        Raises
        ------
        ValueError
            if label is not recognised
        """

        x = np.arange(0,5,1)
        y_values = {
            'low_x':10 + x/10,
            'high_x':20 + x/10,
            'low_y':30 + x/10,
            'high_y':40 + x/10,
            'X':50 + x/10,
            'Y':60 + x/10,
        }
        
        if label not in y_values:
            raise ValueError(f'Unknown sweep[{label}]')
            
        return {'x':x,'y':y_values[label]}


    def get_board_temperature(self):
        return np.random.rand()*3 + 25

    def startup(self):
        print('Starting up testboard')

    def shutdown(self):
        print('Shutting down testboard')

#================================================================
#%% Measurement classes
#================================================================
class MeasActualTemperature(tmpl.AbstractMeasurement):
    name = 'MeasureActualTemperatures'

    def initialise(self):
        #  Break out test resources

        # Set this measurement to execute after temperature condition has
        # been set
        self.run_condition = TemperatureConditions.name


    def meas_sequence(self):

        self.log('-'*40)
        self.log('Recording actual temperatures')

        Tstation = self.station.get_temperature()
        Ttestboard = self.tb.get_board_temperature()

        self.store_data_var('temperature_station_degC',[Tstation])
        self.store_data_var('temperature_board_degC',[Ttestboard])

        self.log(f'Station temperature = {Tstation} degC')
        self.log(f'testboard temperature = {Ttestboard} degC')
        self.log('-'*40)



class PressureSweeper(tmpl.AbstractMeasurement):
    name = 'PressureSweep'

    def initialise(self):
        #  Break out test resources
        self.config.change_me = ''

    def meas_sequence(self):
        
        pressure_label = ['low_x','low_y','high_x','high_y']

        self.store_coords('press',pressure_label)

        for press in pressure_label:
            # Do the measurement
            results = self.tb.sweep(press)

            xlabel = f'sweep_press_var'
            ylabel = f'data_var_press'

            # Store the data
            self.store_coords(xlabel,results['x'])
            self.store_data_var(ylabel,results['y'],
                                coords={'press':press,xlabel:None})

    @tmpl.service
    def example_service(self,axis):
        """
        Example of a service function that other measurements can call

        Parameters
        ----------
        axis : str
            Input argument

        Returns
        -------
        float
            value based on input argument
        """
        # Check the dataset exists
        if self.ds_results is None:
            raise RuntimeError('No data available for example_service')

        # Check the data variable in the dataset exists
        if not 'data_var_press' in self.ds_results:
            raise RuntimeError('data variable[data_var_press] is not in dataset for example_service')

        # Perform the service operation
        if axis=='X':
            return self.ds_results.data_var_press.sel(press=['low_x','high_x']).mean().values
        else:
            return self.ds_results.data_var_press.sel(press=['low_y','high_y']).mean().values
        


class AxisSweeper(tmpl.AbstractMeasurement):
    name = 'AxisSweep'

    def initialise(self):
        #  Break out test resources
        self.config.change_me = ''

        
    def meas_sequence(self):
        
        axes = ['X','Y']

        self.store_coords('axis',axes)

        for axis in axes:
            # Do the measurement
            results = self.tb.sweep(axis)

            xlabel = f'sweep_axis_var'
            ylabel = f'data_var_axis'

            # Store the data
            self.store_coords(xlabel,results['x'])
            self.store_data_var(ylabel,results['y'],
                                coords={'axis':axis,xlabel:None})


class ServiceTester(tmpl.AbstractMeasurement):

    def initialise(self):
        #  Break out test resources
        self.config.change_me = ''


    tmpl.with_services(services=['example_service'])
    def meas_sequence(self):
        
        axes = ['X','Y']
        results = []

        for ax in axes:
            # Call function from another measurement class
            results.append(self.services.example_service(ax))

        # Store the data
        xlabel = 'service_test_axes'
        ylabel = 'service_test_results'
        self.store_coords(xlabel,axes)
        self.store_data_var(ylabel,results,coords={xlabel:None})



class ShutdownTestboard(tmpl.AbstractMeasurement):
    name = 'Shutdown_Testboard'

    def initialise(self):
        #  Break out test resources

        # Set this measurement to execute in the teardown stage
        self.run_condition = self.RUN_STAGE_TEARDOWN


    def meas_sequence(self):
        self.log('Shut down testboard')
        self.tb.shutdown()



class StartupTestboard(tmpl.AbstractMeasurement):
    name = 'Startup_Testboard'

    def initialise(self):
        #  Break out test resources

        # Set this measurement to execute in the startup stage
        self.run_condition = self.RUN_STAGE_STARTUP


    def meas_sequence(self):
        self.log('Startup testboard')
        self.tb.startup()

 
#================================================================
#%% Setup conditions classes
#================================================================

class TemperatureConditions(tmpl.AbstractSetupConditions):
    name = 'temperature_degC'

    def initialise(self):
        #  Break out test resources
        # self.station = self.get_resource('station')

        # Set default values
        self.values = [25,35,45]

    @property
    def actual(self):
        return self.station.get_temperature()

    @property
    def setpoint(self):
        return self.station.get_temperature_setpoint()

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} degC')
        return self.station.set_temperature_setpoint(value)


class HumidityConditions(tmpl.AbstractSetupConditions):
    name = 'humidity_pc'

    def initialise(self):
        #  Break out test resources
        # self.station = self.get_resource('station')

        # Set default values
        self.values = [55,60,70]

    @property
    def actual(self):
        return self.station.get_humidity()

    @property
    def setpoint(self):
        return self.station.get_humidity_setpoint()

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} %')
        return self.station.set_humidity_setpoint(value)


#================================================================
#%% Test Manager class
#================================================================
class ExampleTestSequence(tmpl.AbstractTestManager):
    name = 'ExampleTestSequence'

    def define_setup_conditions(self):
        self.add_setup_condition(TemperatureConditions,cond_name='temperature_degC')
        self.add_setup_condition(HumidityConditions,cond_name='humidity_pc')

    def define_measurements(self):

        # Add measurements in the order that they execute
        self.add_measurement(StartupTestboard)
        self.add_measurement(MeasActualTemperature)
        self.add_measurement(PressureSweeper)
        self.add_measurement(AxisSweeper)
        self.add_measurement(ServiceTester)
        self.add_measurement(ShutdownTestboard)


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
    # Run something
    print('Run')

    resources = {
        'station':ExampleStation(),
        'tb':ExampleTestboard()
        }

    test = ExampleTestSequence(resources)
    test.run()