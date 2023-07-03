"""
Testing services
================================================================
Unit test for mechanics of services

Initially to test changes to tmpl that stop it from running code
in attributes.
"""
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os, time,sys
import unittest
 
# Third party libraries
import numpy as np
import pandas as pd
 
basepath = os.path.dirname(os.path.dirname(__file__))
sys.path.append(basepath)
print(basepath)

# Local libraries
import tmpl
#================================================================
#%% Constants
#================================================================
 
#================================================================
#%% Functions
#================================================================
 
#================================================================
#%% SetupCondition classes
#================================================================

class Cond_with_attribute_error(tmpl.AbstractSetupConditions):
    """
    <Description of condition>
    """
    name = 'error_cond' # Name used in ds_results dataset (optional)

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [1]


    @property
    def actual(self):
        self.log('Run actual')
        raise RuntimeError('This attribute causes an error')
        return 1

    @property
    def setpoint(self):
        self.log('Run setpoint')
        return 2

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} ')
        # TODO :<Setpoint code>
        return 3



#================================================================
#%% Measurement classes
#================================================================

class Meas1(tmpl.AbstractMeasurement):
    """
    <Description of measurement>

    """

    def initialise(self):
        pass

    def meas_sequence(self):
        """
        <More description (optional)>
        """
        # TODO: Measurement code goes here
        pass

    @tmpl.service
    def my_service(self):
        return 4
        
        


#================================================================
#%% TestManager classes
#================================================================

class Seq1(tmpl.AbstractTestManager):
    """
    <Description of test sequence>
    """

    def define_setup_conditions(self):
        """
        Add the setup conditions here in the order that they should be set
        """
        self.add_setup_condition(Cond_with_attribute_error)


    def define_measurements(self):
        """
        Add measurements here in the order of execution
        """

        # Setup links to all the measurements
        self.add_measurement(Meas1)


    def initialise(self):
        """
        Add custom information here
        """
        
        self.information.serial_number = 'example_sn'
        self.information.part_number = 'example_pn'
        # Add more here ...
 
#================================================================
#%% Classes
#================================================================
class TestServices(unittest.TestCase):
 
    def setUp(self):
        pass
 
 
    def tearDown(self):
        pass

    def test_dummy(self):
        self.assertTrue(True)

    def test_instantiate(self):
        """
        Test that a TestManager can be instantiated without running
        code in the actual/setpoint attributes of SetupCondition 
        classes
        """

        # This line should run without any errors being thrown
        seq = Seq1({})

        # Check the services were found
        self.assertTrue('my_service' in seq.services_available)
 
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
        suite.addTest(TestServices('test_dummy'))
        
        runner = unittest.TextTestRunner()
        runner.run(suite)