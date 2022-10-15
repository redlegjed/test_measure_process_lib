"""
TMPL Code generator
================================================================
Utility functions for generating code templates for TMPL modules
and classes.

Example usage
-------------

Generate a module file with SetupCondition, Measurement and TestManager
class templates

>>> tmpl.make_module(filename)

Generate template with named classes

>>> tmpl.make_module(filename,condition=['Cond1','Cond2'],meas=['Meas1','Meas2'],seq=['Seq1','Seq2'])

"""
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os, pathlib
import copy
 
# Third party libraries
import numpy as np
import pandas as pd
 
#================================================================
#%% Templates
#================================================================
TEMPLATE_CONDITIONS = '''
class <CONDITION_NAME>(tmpl.AbstractSetupConditions):
    """
    <Description of condition>
    """
    #name = '<name_in_dataset' # Name used in ds_results dataset (optional)

    def initialise(self):
        """
        Initialise default values and any other setup
        """

        # Set default values
        self.values = [<values>]


    @property
    def actual(self):
        return <Return value code>

    @property
    def setpoint(self):
        return <Return setpoint code>

    @setpoint.setter
    def setpoint(self,value):
        self.log(f'Setpoint = {value} ')
        # TODO :<Setpoint code>
        return <Setpoint value>

'''

TEMPLATE_MEASUREMENT = '''
class <MEASUREMENT_NAME>(tmpl.AbstractMeasurement):
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

        # Set up configuration vaules
        self.config.<param> = <value>
        

    def meas_sequence(self):
        """
        <More description (optional)>
        """
        # TODO: Measurement code goes here
        pass
        
        
'''

TEMPLATE_MANAGER = '''
class <MANAGER_NAME>(tmpl.AbstractTestManager):
    """
    <Description of test sequence>
    """

    def define_setup_conditions(self):
        """
        Add the setup conditions here in the order that they should be set
        """
<CONDITION_DEFINITIONS>


    def define_measurements(self):
        """
        Add measurements here in the order of execution
        """

        # Setup links to all the measurements
<MEASUREMENT_DEFINITIONS>


    def initialise(self):
        """
        Add custom information here
        """
        
        self.information.serial_number = 'example_sn'
        self.information.part_number = 'example_pn'
        # Add more here ...
 
'''

TEMPLATE_MODULE = '''\"\"\"
Module: <MODULE_FILENAME>
================================================================
<Description of module>

SetupCondition classes:
<CONDITION_CLASSES>

Measurement classes:
<MEASUREMENT_CLASSES>

TestManager classes:
<MANAGER_CLASSES>



This module is based on the "Test, Measure, Process Library" (TMPL)
framework for organising measurement code.
See: https://github.com/redlegjed/test_measure_process_lib

\"\"\"

#================================================================
\#%% Imports
#================================================================
# Standard library
import os
import time

# Third party libraries
import numpy as np
import pandas as pd
import tmpl

#================================================================
\#%% SetupCondition classes
#================================================================
<CONDITION_TEXT>

#================================================================
\#%% Measurement classes
#================================================================
<MEASUREMENT_TEXT>

#================================================================
\#%% TestManager classes
#================================================================
<MANAGER_TEXT>
'''
 
#================================================================
#%% Functions
#================================================================
def make_condition(name):
    """
    Make code for a single SetupCondition class

    Parameters
    ----------
    name : str
        Name of SetupConditions class

    Returns
    -------
    str
        text of class definition code
    """
    txt = copy.deepcopy(TEMPLATE_CONDITIONS)
    return txt.replace('<CONDITION_NAME>',name)

def make_measurement(name):
    """
    Make code for a single Measurement class

    Parameters
    ----------
    name : str
        Name of Measurement class

    Returns
    -------
    str
        text of class definition code
    """
    txt = copy.deepcopy(TEMPLATE_MEASUREMENT)
    return txt.replace('<MEASUREMENT_NAME>',name)
 

def make_manager(name,conditions=['DefaultCondition'],meas=['DefaultMeasurement']):
    """
    Make code for a single TestManager class

    Parameters
    ----------
    name : str
        Name of TestManager class
    conditions : list, optional
        List of names of SetupCondition classes, by default ['DefaultCondition']
    meas : list, optional
        List of names of Measurement classes, by default ['DefaultMeasurement']

    Returns
    -------
    str
        text of class definition code
    """
    txt = copy.deepcopy(TEMPLATE_MANAGER)
    txt = txt.replace('<MANAGER_NAME>',name)

    # Make conditions lines
    cond_txt = [f'        self.add_condition({c})' for c in conditions]
    
    # Make conditions lines
    meas_txt = [f'        self.add_measurement({m})' for m in meas]

    txt = txt.replace('<CONDITION_DEFINITIONS>','\n'.join(cond_txt))
    txt = txt.replace('<MEASUREMENT_DEFINITIONS>','\n'.join(meas_txt))

    return txt


def make_module(filename,conditions=['DefaultCondition'],
                    meas=['DefaultMeasurement'],
                    seq=['DefaultSeq'],return_text=False):
    """
    Make a module file with auto-generated code for TMPL classes.

    Specifiy the names of the SetupConditions, Measurement and TestManager
    classes in the input arguments. A code template for each class will be
    added to the module file.

    The module is divided into sections:
    * Module doc string: The text at the top of the file in triple quotes
    * Standard imports
    * SetupCondition classes
    * Measurement classes
    * TestManager classes

    Example usage
    --------------
    Make lists of class names
    >>> cond = ['Temperature','Humidity','Pressure']
    >>> meas = ['VoltageSweep','CurrentSweep','PostProcess']
    >>> seq = ['Calibrate','MainMeasure']

    Name of module file (full paths supported as well)
    >>> name = 'BigExperiment2.py'

    Generate module file
    >>> make_module(name,conditions=cond,meas=meas,seq=seq)

    Parameters
    ----------
    filename : str
        full filename for module file to be created
    conditions : list, optional
        List of names of SetupCondition classes, by default ['DefaultCondition']
    meas : list, optional
        List of names of Measurement classes, by default ['DefaultMeasurement']
    seq : list, optional
        List of names of TestManager classes, by default ['DefaultSeq']
    return_text : bool, optional
        If True then the text of the module is returned as a string
        otherwise the text is save to a file, by default False

    Returns
    -------
    str or None
        text string if return_text is True otherwise None
    """


    # Create basic text
    # ==============================
    txt = copy.deepcopy(TEMPLATE_MODULE)

    # Add name to top
    file = pathlib.Path(filename)
    txt = txt.replace('<MODULE_FILENAME>',file.stem)

    # List of condition classes
    # ==============================
    rep_txt = [f'* {s} :' for s in conditions]
    txt = txt.replace('<CONDITION_CLASSES>','\n'.join(rep_txt))

    # List of Measurement classes
    # ==============================
    rep_txt = [f'* {s} :' for s in meas]
    txt = txt.replace('<MEASUREMENT_CLASSES>','\n'.join(rep_txt))

    # List of TestManager classes
    # ==============================
    rep_txt = [f'* {s} :' for s in seq]
    txt = txt.replace('<MANAGER_CLASSES>','\n'.join(rep_txt))

    # Text of condition classes
    # ==============================
    rep_txt = [make_condition(s) for s in conditions]
    txt = txt.replace('<CONDITION_TEXT>','\n'.join(rep_txt))
    
    # Text of measurement classes
    # ==============================
    rep_txt = [make_measurement(s) for s in meas]
    txt = txt.replace('<MEASUREMENT_TEXT>','\n'.join(rep_txt))
    
    # Text of test manager classes
    # ==============================
    rep_txt = [make_manager(s,conditions=conditions,meas=meas) for s in seq]
    txt = txt.replace('<MANAGER_TEXT>','\n'.join(rep_txt))

    # Have to escape the #%% because VSCode thinks it's a notebook
    # - undo this here
    txt = txt.replace(r'\#','#')
    
    if return_text:
        return txt

    file.write_text(txt)


#================================================================
#%% Classes
#================================================================

#================================================================
#%% Runner
#================================================================

if __name__ == '__main__':
    cond = ['Temperature','Humidity','Pressure']
    meas = ['VoltageSweep','CurrentSweep','PostProcess']
    seq = ['Calibrate','MainMeasure']

    name = 'BigExperiment2.py'

    print(make_module(name,conditions=cond,meas=meas,seq=seq))
 