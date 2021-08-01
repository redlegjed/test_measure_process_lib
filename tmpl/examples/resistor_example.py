'''
Simple resistor measurement example
================================================================
Classes and functions to support the simple resistor measurement
examples from main README.md.

Defines the VoltageSupply() and Ammeter() classes used in the simple 
resistor example
'''
 
 
#================================================================
#%% Imports
#================================================================
 
# Third party libraries
import numpy as np
 

 
#================================================================
#%% Resistor model
#================================================================
# Define a simple class for a resistor that allows the experimental
# conditions to be setup and for the voltage across the resistor to 
# be set.
class ResistorModel():
    """
    Simple resistor model.
    """
    def __init__(self,resistance_ohms,tolerance_pc=1.0) -> None:
        
        # Basics
        # ------------
        self.resistance_base_ohms = resistance_ohms
        self.tolerance_pc = tolerance_pc

        # Environmental conditions
        # ------------------------------
        # These are set by external functions

        self.voltage = 0.0
        self.temperature_degC = 25.0
        self.humidity_pc = 40.0

        # Define some relations to temperature and humidity
        # - purely to generate different values according to these conditions
        self.temperature_factor = 1
        self.humidity_factor = 1/100

        

    @property
    def resistance_ohms(self):
        """
        Return resistance at current conditions
        """
        # Base resistance value
        R_ohms = self.resistance_base_ohms*(1 + self.tolerance_pc/100)

        # Additional resistance due to temperature and humidity
        R_T_ohms = self.temperature_degC*self.temperature_factor
        R_H_ohms = self.humidity_pc*self.humidity_factor

        return R_ohms + R_T_ohms + R_H_ohms


    @property
    def current_A(self):
        """
        Return current through resistor at current conditions
        """
        return self.voltage/self.resistance_ohms
 
#================================================================
#%% Virtual Test instrument classes
#================================================================


class VoltageSupply():
    """
    Example virtual test instrument class for voltage supply

    >>> resistor = ResistorModel()
    >>> supply = VoltageSupply(resistor)
    """

    def __init__(self,resistor) -> None:
        self.resistor = resistor

    @property
    def voltage_set_V(self):
        """
        Set Voltage on resistor

        Returns
        -------
        float
            voltage
        """
        return self.resistor.voltage

    @voltage_set_V.setter
    def voltage_set_V(self,voltage):
        self.resistor.voltage = voltage

    @property
    def actual_voltage_V(self):
        """
        Return Voltage on resistor
        (set point + small amount of noise)

        Returns
        -------
        float
            actual voltage
        """
        return self.resistor.voltage*(1 + np.random.rand()/100)
 

class Ammeter():
    """
    Example virtual test instrument class for ammeter

    >>> resistor = ResistorModel()
    >>> supply = Ammeter(resistor)
    """

    def __init__(self,resistor) -> None:
        self.resistor = resistor

    @property
    def current_A(self):
        return self.resistor.current_A


