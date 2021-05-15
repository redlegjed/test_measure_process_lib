'''
Example of test class setup using test_measure_process library
================================================================
Define a full set of classes using the TMPL library

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

import tmpl_core as TMPL
 
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
            'XI':10 + x/10,
            'XQ':20 + x/10,
            'YI':30 + x/10,
            'YQ':40 + x/10,
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
class MeasActualTemperature(TMPL.AbstractMeasurement):
    name = 'MeasureActualTemperatures'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')
        self.tb = self.get_resource('testboard')

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



class TribSweeper(TMPL.AbstractMeasurement):
    name = 'TribSweep'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')
        self.tb = self.get_resource('testboard')


    def meas_sequence(self):
        
        tribs = ['XI','XQ','YI','YQ']

        self.store_coords('trib',tribs)

        for trib in tribs:
            # Do the measurement
            results = self.tb.sweep(trib)

            xlabel = f'sweep_trib_var'
            ylabel = f'data_var_trib'

            # Store the data
            self.store_coords(xlabel,results['x'])
            self.store_data_var(ylabel,results['y'],
                                coords={'trib':trib,xlabel:None})

    @TMPL.service
    def example_service(self,pol):
        """
        Example of a service function that other measurements can call

        Parameters
        ----------
        pol : str
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
        if not 'data_var_trib' in self.ds_results:
            raise RuntimeError('data variable[data_var_trib] is not in dataset for example_service')

        # Perform the service operation
        if pol=='X':
            return self.ds_results.data_var_trib.sel(trib=['XI','XQ']).mean().values
        else:
            return self.ds_results.data_var_trib.sel(trib=['YI','YQ']).mean().values
        


class PolSweeper(TMPL.AbstractMeasurement):
    name = 'PolSweep'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')
        self.tb = self.get_resource('testboard')



    def meas_sequence(self):
        
        pols = ['X','Y']

        self.store_coords('pol',pols)

        for pol in pols:
            # Do the measurement
            results = self.tb.sweep(pol)

            xlabel = f'sweep_pol_var'
            ylabel = f'data_var_pol'

            # Store the data
            self.store_coords(xlabel,results['x'])
            self.store_data_var(ylabel,results['y'],
                                coords={'pol':pol,xlabel:None})



class ShutdownTestboard(TMPL.AbstractMeasurement):
    name = 'Shutdown_Testboard'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')
        self.tb = self.get_resource('testboard')

        # Set this measurement to execute in the teardown stage
        self.run_condition = self.RUN_COND_TEARDOWN


    def meas_sequence(self):
        self.log('Shut down testboard')
        self.tb.shutdown()



class StartupTestboard(TMPL.AbstractMeasurement):
    name = 'Startup_Testboard'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')
        self.tb = self.get_resource('testboard')

        # Set this measurement to execute in the startup stage
        self.run_condition = self.RUN_COND_STARTUP


    def meas_sequence(self):
        self.log('Startup testboard')
        self.tb.startup()

 
#================================================================
#%% Setup conditions classes
#================================================================

class TemperatureConditions(TMPL.AbstractSetupConditions):
    name = 'temperature_degC'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')

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


class HumidityConditions(TMPL.AbstractSetupConditions):
    name = 'humidity_pc'

    def initialise(self):
        #  Break out test resources
        self.station = self.get_resource('station')

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
class ExampleTestSequence(TMPL.AbstractTestManager):
    name = 'ExampleTestSequence'

    def define_setup_conditions(self):
        self.conditions['temperature_degC'] = TemperatureConditions(self.resources,values=[25,35,45])
        self.conditions['humidity_pc'] = HumidityConditions(self.resources,values=[25,35,45])

    def define_measurements(self):

        # Setup links to all the measurements
        self.meas[StartupTestboard.name] = StartupTestboard(self.resources)
        
        self.meas[MeasActualTemperature.name] = MeasActualTemperature(self.resources)
        self.meas['trib_sweep'] = TribSweeper(self.resources)
        self.meas['pol_sweep'] = PolSweeper(self.resources)

        self.meas[ShutdownTestboard.name] = ShutdownTestboard(self.resources)

        


 
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run something
    print('Run')

    resources = {
        'station':ExampleStation(),
        'testboard':ExampleTestboard()
        }

    test = ExampleTestSequence(resources)