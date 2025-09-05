"""
Testing sequence with no setup conditions defined
================================================================
Make a sequence that does not define any setup conditions in
define_setup_conditions().

Originally created to test removing the "default" condition 
"""
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import sys, os, time
# import pathlib
import unittest
 
# Third party libraries
 
basepath = os.path.dirname(os.path.dirname(__file__))
sys.path.append(basepath)
print(basepath)

import tmpl

#================================================================
#%% Measurements
#================================================================
class MeasWithOwnCoords(tmpl.AbstractMeasurement):
    """
    Dummy measurement that defines it's own coordinates

    """

    def meas_sequence(self):

        coords = ['dog', 'cat', 'horse']
        data = [1,2,3]

        self.store_coords('home','My house')
        self.store_coords('animal',coords)
        self.store_data_var('weight',data, coords=['animal'])

 
#================================================================
#%% Sequences
#================================================================
class Sequence(tmpl.AbstractTestManager):
    """
    Sequence for testing no setup conditions
    """

    def define_setup_conditions(self):
        return super().define_setup_conditions()

    def define_measurements(self):
        self.add_measurement(MeasWithOwnCoords)

    def initialise(self):

        self.information.home = 'My_house'
        self.information.date = '29th Feb 1984'

 
#================================================================
#%% Unit tests 
#================================================================
class TestNoConditionsRemoveDefault(unittest.TestCase):
 
    def setUp(self):
        pass
 
 
    def tearDown(self):
        pass

    def test_dummy(self):
        self.assertTrue(True)

    def test_results_have_no_default(self):
        """
        Test that a sequence with nothing defined in 
        define_setup_conditions() removes the 'default' condition

        """

        # This line should run without any errors being thrown
        test = Sequence()
        test.run()
        ds_results = test.ds_results

        # Check for the 'default' condition, it should not be there
        self.assertFalse('default' in ds_results.coords, msg='default condition was not removed')
 
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run something
    print('Run')
    all_tests = True

    if all_tests:
        unittest.main()
        print('Run')
    else:
        suite = unittest.TestSuite()

        # suite.addTest(TestMeasurement('test_dummy'))
        suite.addTest(TestNoConditionsRemoveDefault('test_results_have_no_default'))
        
        runner = unittest.TextTestRunner()
        runner.run(suite)
 
# #================================================================
# #%% Runner
# #================================================================
#  
# if __name__ == '__main__':
#     # Run something
#     print('Run')
#     test = Sequence()
#     test.remove_default_condition = False
#     test.run()
#
#     print(f'remove_defaults flag = {test.remove_default_condition}')
#
#     ds_results = test.ds_results
#     # Main results
#     print('Main results:\n-----------------------------------')
#     print(ds_results)
#
#     print('Measurement results\n----------------------')
#     print(test.meas.MeasWithOwnCoords.ds_results)

