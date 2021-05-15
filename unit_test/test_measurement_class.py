'''
Testing the Measurement class
================================================================
Unit tests to verify the functionality of classes derived from
AbstractMeasurement

'''
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os, time, sys
import unittest
 
# Third party libraries
import numpy as np
import pandas as pd
import xarray as xr

basepath = os.path.dirname(os.path.dirname(__file__))
sys.path.append(basepath)
print(basepath)

# Local libraries
from tmpl_core import AbstractMeasurement
 
#================================================================
#%% Constants
#================================================================
 
#================================================================
#%% Functions
#================================================================

#================================================================
#%% Classes
#================================================================
class Meas1(AbstractMeasurement):
    name = 'Meas1'
    activate_bad_data_vars = False

    
    def meas_sequence(self,tag=0):

        # Get conditions
        temperature_degc = self.current_conditions.get('temperature_degc',10)
        humidity_pc = self.current_conditions.get('humidity_pc',1)
        
        # First sweep
        sweep_var1 = np.array([1,2,3])
        data_var1 = 100*sweep_var1 + temperature_degc + humidity_pc/100 + tag/10000
        data_var2 = 200*sweep_var1 + temperature_degc + humidity_pc/100 + tag/10000

        self.store_coords('sweep_var1',sweep_var1)
        self.store_data_var('data_var1_1',data_var1,coords=['sweep_var1'])
        self.store_data_var('data_var1_2',data_var2,coords=['sweep_var1'])

        # Second sweep
        sweep_var2 = np.array([1,2,3])
        data_var1 = 1000*sweep_var2 + temperature_degc + humidity_pc/100 + tag/10000
        data_var2 = 2000*sweep_var2 + temperature_degc + humidity_pc/100 + tag/10000

        self.store_coords('sweep_var2',sweep_var2)
        self.store_data_var('data_var2_1',data_var1,coords=['sweep_var2'])
        self.store_data_var('data_var2_2',data_var2,coords=['sweep_var2'])

        # Spot values
        self.store_data_var('Light_level',12)

        # Data with no coordinates defined
        if self.activate_bad_data_vars:
            self.store_data_var('data_var_uc',data_var2*3,coords=['unknown_coord'])
            self.store_data_var('data_var_no_coords',data_var2*3) # designed to cause an error


 
#================================================================
#%% Tests
#================================================================
class TestMeasurement(unittest.TestCase):
 
    def setUp(self):
        pass
 
 
    def tearDown(self):
        pass

    def test_dummy(self):
        meas = Meas1({})
 
        self.assertTrue(True)


    def test_no_conditions(self):


        # Create measurement
        meas = Meas1({})

        # Run measurements at different conditions
        ok = meas.run()
        self.assertTrue(ok,msg=f'Measurement [{meas.name}] failed to run')
        ds_results1 = meas.ds_results

        # Check dataset
        req_coords = ['default','sweep_var1','sweep_var2']
        req_data_vars = ['data_var1_1','data_var1_2','data_var2_1','data_var2_2','Light_level']

        missing_coords = [c for c in req_coords if c not in ds_results1.coords]
        missing_data_vars = [d for d in req_data_vars if d not in ds_results1]

        self.assertTrue(missing_coords==[],msg=f'Dataset is missing coordinates {missing_coords}')
        self.assertTrue(missing_data_vars==[],msg=f'Dataset is missing data vars {missing_data_vars}')

        print('Done')



    def test_single_conditions(self):

        # Define conditions
        cond1 = dict(temperature_degC=25,humidity_pc=45)

        # Create measurement
        meas = Meas1({})

        # Run measurements at different conditions
        ok = meas.run(conditions=cond1)
        self.assertTrue(ok,msg=f'Measurement [{meas.name}] failed to run')
        ds_results1 = meas.ds_results

        # Check dataset
        req_coords = ['temperature_degC','humidity_pc','sweep_var1','sweep_var2']
        req_data_vars = ['data_var1_1','data_var1_2','data_var2_1','data_var2_2','Light_level']

        missing_coords = [c for c in req_coords if c not in ds_results1.coords]
        missing_data_vars = [d for d in req_data_vars if d not in ds_results1]

        self.assertTrue(missing_coords==[],msg=f'Dataset is missing coordinates {missing_coords}')
        self.assertTrue(missing_data_vars==[],msg=f'Dataset is missing data vars {missing_data_vars}')


        print('Done')


    def test_multiple_conditions(self):

        # Define conditions
        cond1 = dict(temperature_degC=25,humidity_pc=45)
        cond2 = dict(temperature_degC=45,humidity_pc=32)

        # Expected content of results datasets
        req_coords = ['temperature_degC','humidity_pc','sweep_var1','sweep_var2']
        req_data_vars = ['data_var1_1','data_var1_2','data_var2_1','data_var2_2','Light_level']


        # Create measurement
        meas = Meas1({})

        # Run measurements at different conditions
        # =========================================
        # Condition 1
        # ------------------------------
        ok = meas.run(conditions=cond1,tag=1)
        self.assertTrue(ok,msg=f'Measurement [{meas.name}] failed to run')
        ds_results1 = meas.ds_results

        # Check dataset
        missing_coords = [c for c in req_coords if c not in ds_results1.coords]
        missing_data_vars = [d for d in req_data_vars if d not in ds_results1]

        self.assertTrue(missing_coords==[],msg=f'Dataset 1 is missing coordinates {missing_coords}')
        self.assertTrue(missing_data_vars==[],msg=f'Dataset 1 is missing data vars {missing_data_vars}')

        # Condition 2
        # ------------------------------
        ok = meas.run(conditions=cond2,tag=2)
        self.assertTrue(ok,msg=f'Measurement [{meas.name}] failed to run')
        ds_results2 = meas.ds_results

        # Check dataset
        missing_coords = [c for c in req_coords if c not in ds_results2.coords]
        missing_data_vars = [d for d in req_data_vars if d not in ds_results2]

        self.assertTrue(missing_coords==[],msg=f'Dataset 2 is missing coordinates {missing_coords}')
        self.assertTrue(missing_data_vars==[],msg=f'Dataset 2 is missing data vars {missing_data_vars}')


        # Repeat conditions 1 and overwrite data
        # ------------------------------
        ok = meas.run(conditions=cond1,tag=3)
        self.assertTrue(ok,msg=f'Measurement [{meas.name}] failed to run')
        ds_results1_repeat = meas.ds_results

        # Check dataset
        missing_coords = [c for c in req_coords if c not in ds_results1_repeat.coords]
        missing_data_vars = [d for d in req_data_vars if d not in ds_results1_repeat]

        self.assertTrue(missing_coords==[],msg=f'Dataset 1 repeat is missing coordinates {missing_coords}')
        self.assertTrue(missing_data_vars==[],msg=f'Dataset 1 repeat is missing data vars {missing_data_vars}')


        print('Done')





#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # all_tests = True
    all_tests = False

    if all_tests:
        unittest.main()
        print('Run')
    else:
        suite = unittest.TestSuite()

        # suite.addTest(TestMeasurement('test_dummy'))
        suite.addTest(TestMeasurement('test_no_conditions'))
        suite.addTest(TestMeasurement('test_single_conditions'))
        suite.addTest(TestMeasurement('test_multiple_conditions'))
        
        
        runner = unittest.TextTestRunner()
        runner.run(suite)