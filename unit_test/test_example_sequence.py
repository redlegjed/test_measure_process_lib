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
# from test_measure_process import AbstractMeasurement
from example_test_setup import ExampleTestSequence,ExampleTestboard,ExampleStation

#================================================================
#%% Constants
#================================================================
 
#================================================================
#%% Functions
#================================================================


 
#================================================================
#%% Tests
#================================================================
class TestExampleSequence(unittest.TestCase):
 
    def setUp(self):
        resources = {
            'station':ExampleStation(),
            'testboard':ExampleTestboard()
            }

        self.testseq = ExampleTestSequence(resources)
 
 
    def tearDown(self):
        pass

    def test_dummy(self):
        
 
        self.assertTrue(True)


    def test_got_conditions_and_meas(self):
        """
        Check conditions and measurements are in place
        """

        self.assertTrue(hasattr(self.testseq,'conditions'),msg='No conditions property')
        self.assertTrue(hasattr(self.testseq,'meas'),msg='No meas property')


        cond_names = ['temperature_degC','humidity_pc']
        for cond_name in cond_names:
            self.assertTrue(cond_name in self.testseq.conditions,
                msg=f'Setup conditions [{cond_name}] failed to be loaded')

        meas_names = ['trib_sweep','pol_sweep']
        for meas_name in meas_names:
            self.assertTrue(meas_name in self.testseq.meas,
                msg=f'Meas [{meas_name}] failed to be loaded')


        
    def test_conditions_table(self):
        """
        Check the iteration works
        """

        cond_table = self.testseq.conditions_table
        for cond in cond_table:
            print(cond)
        # just see if it works for now


    def test_running_default_conditions(self):

        self.testseq.run()
        # just see if it works for now
        print(self.testseq.ds_results)


    def test_stacking_multiple_runs(self):
        """
        Run test sequence multiple times with different information
        data and try to stack the resulting datasets
        """
        nRuns = 4

        results = []
        for run in range(nRuns):
            self.testseq.information.serial_number = f'SN_{run}'
            self.testseq.information.part_number = 'PN_1'
            self.testseq.run()
            results.append(self.testseq.ds_results)

        # concat only works on one dimension
        ds_all = xr.concat(results,dim='serial_number')

        self.assertTrue('serial_number' in ds_all.coords,
            msg='serial_number is not a coordinate')

        self.assertEqual(nRuns,ds_all.coords['serial_number'].size,
            msg='Serial number coordinate is wrong length')




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

        # suite.addTest(TestExampleSequence('test_dummy'))
        # suite.addTest(TestExampleSequence('test_got_conditions_and_meas'))
        # suite.addTest(TestExampleSequence('test_conditions_table'))
        # suite.addTest(TestExampleSequence('test_running_default_conditions'))
        suite.addTest(TestExampleSequence('test_stacking_multiple_runs'))
        
        
        runner = unittest.TextTestRunner()
        runner.run(suite)