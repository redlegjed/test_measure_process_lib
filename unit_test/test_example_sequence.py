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
DATAFILE_PATH = os.path.join(basepath,'unit_test','data_files')
 
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


    def test_save_results(self):
        """
        Save data after a test run in various formats and check the 
        files are stored.
        """

        data_filename_json = os.path.join(DATAFILE_PATH,'test_data.json')
        data_filename_excel = os.path.join(DATAFILE_PATH,'test_data.xlsx')

        self.testseq.run()

        self.testseq.save(data_filename_json)
        self.testseq.save(data_filename_excel,format='excel')

        self.assertTrue(os.path.exists(data_filename_json),
            msg='Failed to save json file')

        self.assertTrue(os.path.exists(data_filename_excel),
            msg='Failed to save excel file')

        # Clean up
        if os.path.exists(data_filename_json):
            os.remove(data_filename_json)

        if os.path.exists(data_filename_excel):
            os.remove(data_filename_excel)


    def test_save_and_load_results(self):
        """
        Save data after a test run and load it back
        """

        data_filename_json = os.path.join(DATAFILE_PATH,'test_data.json')
        

        self.testseq.run()

        self.testseq.save(data_filename_json)
        
        self.assertTrue(os.path.exists(data_filename_json),
            msg='Failed to save json file')

        # Create new test sequence to load back the file
        new_seq = ExampleTestSequence({},offline_mode=True)
        new_seq.load(data_filename_json)

        # Compare datasets
        self.assertTrue(self.testseq.ds_results.equals(new_seq.ds_results),
            msg='Reloaded Results data is not equal')


        # Clean up
        if os.path.exists(data_filename_json):
            os.remove(data_filename_json)

        

        



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
        # suite.addTest(TestExampleSequence('test_stacking_multiple_runs'))
        # suite.addTest(TestExampleSequence('test_save_results'))
        suite.addTest(TestExampleSequence('test_save_and_load_results'))
        
        
        runner = unittest.TextTestRunner()
        runner.run(suite)