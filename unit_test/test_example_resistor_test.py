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
from xarray.core.utils import V

basepath = os.path.dirname(os.path.dirname(__file__))
sys.path.append(basepath)
print(basepath)

# Local libraries
# from test_measure_process import AbstractMeasurement
from tmpl.examples.example_resistor_test import (ExampleTestSequence,ResistorModel,
                                    VoltageSupply,set_temperature,
                                    set_humidity)

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
        res1 = ResistorModel(100,tolerance_pc=1.0)

        self.resources = {
            'set_temperature':set_temperature,
            'set_humidity': set_humidity,
            'voltage_supply':VoltageSupply(),
            'resistor':res1,
            }

        self.testseq = ExampleTestSequence(self.resources)
 
 
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

        meas_names = ['VoltageSweep','Stabilise']
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

        self.assertTrue(self.testseq.last_error=='',msg='Test run failed')


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

        # Compare datasets for test managers
        self.assertTrue(self.testseq.ds_results.equals(new_seq.ds_results),
            msg='Reloaded Results data for test manager is not equal')

        # Compare datasets for measurements
        for meas_name in self.testseq.meas:
            if len(self.testseq.meas[meas_name].ds_results.data_vars)==0:
                continue

            print(meas_name)
            self.assertTrue(self.testseq.meas[meas_name].ds_results.equals(new_seq.meas[meas_name].ds_results),
                msg=f'Reloaded Results data for meas[{meas_name}] is not equal')



        # Clean up
        if os.path.exists(data_filename_json):
            os.remove(data_filename_json)

        
    def test_custom_config(self):
        """
        Test adding custom config parameters to test sequence
        """

        custom_config = {'param1':1,'param2':2}
        seq = ExampleTestSequence(self.resources,config=custom_config)

        for k,v in custom_config.items():
            self.assertTrue(k in seq.config,msg=f'Test parameter [{k}] not in config dict')
            self.assertEqual(seq.config[k],v,msg=f'Test parameter [{k}] does not have correct value [{v}]')

        

    def test_global_data_passing(self):
        """
        Test global data can be read/written from all TMPL objects
        """

        # Make the Test manager
        seq = ExampleTestSequence(self.resources)


        # Test manager -> Meas, Conditions
        # ----------------------------------
        # Put global data into test manager
        seq.global_data.test_01 = 1

        # Read from meas object
        self.assertTrue('test_01' in seq.meas.VoltageSweep.global_data,
                msg='Measurement does not have test_01 in global data')

        self.assertEqual(seq.meas.VoltageSweep.global_data.test_01,1,
            msg='Measurement does not have correct value in global data for test_01')

        # Read from conditions object
        self.assertTrue('test_01' in seq.conditions.humidity_pc.global_data,
                msg='Condition does not have test_01 in global data')

        self.assertEqual(seq.conditions.humidity_pc.global_data.test_01,1,
            msg='Condition does not have correct value in global data for test_01')

        # Meas -> TestManager,Conditions
        # --------------------------------
        # Put global data into measurement
        seq.meas.VoltageSweep.global_data.test_02 = 2

        # Read from conditions object
        self.assertTrue('test_02' in seq.conditions.humidity_pc.global_data,
                msg='Condition does not have test_02 in global data')

        self.assertEqual(seq.conditions.humidity_pc.global_data.test_02,2,
            msg='Condition does not have correct value in global data for test_02')

        # Read from TestManager object
        self.assertTrue('test_02' in seq.global_data,
                msg='TestManager does not have test_02 in global data')

        self.assertEqual(seq.global_data.test_02,2,
            msg='TestManager does not have correct value in global data for test_02')

        
        # Conditions -> TestManager,Meas
        # --------------------------------
        # Put global data into measurement
        seq.conditions.humidity_pc.global_data.test_03 = 3

        # Read from meas object
        self.assertTrue('test_03' in seq.meas.VoltageSweep.global_data,
                msg='Measurement does not have test_03 in global data')

        self.assertEqual(seq.meas.VoltageSweep.global_data.test_03,3,
            msg='Measurement does not have correct value in global data for test_03')

        # Read from TestManager object
        self.assertTrue('test_03' in seq.global_data,
                msg='TestManager does not have test_03 in global data')

        self.assertEqual(seq.global_data.test_03,3,
            msg='TestManager does not have correct value in global data for test_03')

    def test_global_config_precedence(self):
        """
        Test that global config data overwrites local config data
        """
        #  Make global config
        global_config = {'voltage_sweep':np.linspace(0,20)}

        # Make the Test manager
        seq = ExampleTestSequence(self.resources,config=global_config)

        # Check 'voltage_sweep' in measurement
        self.assertTrue(max(seq.meas.VoltageSweep.config.voltage_sweep)==20,
            msg='Global config did not overwrite local config')


    def test_services(self):
        """
        Check services are available and being used
        """    

        service_labels = ['Amps_to_mA']

        # Check services were added
        for serv in service_labels:
            self.assertIn(serv,self.testseq.services,
                    msg=f'Missing service: {serv}')

        # Run sequence and check for evidence of services being used by
        # looking for the data variables that should have been calculated
        data_vars = ['current_mA']

        self.testseq.run()
        for dv in data_vars:
            self.assertIn(dv,self.testseq.ds_results,
                    msg=f'Service testing: missing data var : {dv}')

#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    all_tests = True
    # all_tests = False

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
        # suite.addTest(TestExampleSequence('test_save_and_load_results'))
        # suite.addTest(TestExampleSequence('test_custom_config'))
        # suite.addTest(TestExampleSequence('test_global_data_passing'))
        # suite.addTest(TestExampleSequence('test_global_config_precedence'))
        suite.addTest(TestExampleSequence('test_services'))
        
        
        runner = unittest.TextTestRunner()
        runner.run(suite)