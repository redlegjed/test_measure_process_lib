'''
Test, measure, process library core classes
================================================================
Define a class framework for running tests.

The framework consists of test classes that contain sub classes
for implementing setup conditions and measurements.

The framework is designed to use xarray datasets as the main 
storage.

TestManager
- SetupCondition
- Measurement
- Service

Example of use
--------------

Initialise test

>>> test = TestManager_mymeas(station,uut)

Setup conditions under which test is to be run

>>> test.setup.temperature.values = [25,40,75]
>>> test.setup.wavelength.values = [1528,1545,1565]

Setup which measurements are to be run

>>> test.meas.dark_currents.enable = False
>>> test.meas.InnerSweep.enable = True
>>> test.meas.OuterSweep.enable = True

Run test over all setup conditions

>>> test.run()

Get results as xarray Dataset

>>> test.ds_results

Get individual results from a measurement

>>> test.meas.InnerSweep.ds_results

Run individual measurement with specified conditions

>>> conditions = dict(temperature_degC=34,wavelength_nm=1550)
>>> test.meas.InnerSweep.run(conditions)

Run measurement without specifiying conditions

>>> test.meas.InnerSweep.run()


'''
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os, time
import abc
import traceback
import itertools
import copy
import inspect

#from collections import OrderedDict
 
# Third party libraries
import numpy as np
import pandas as pd
import xarray as xr
# from xarray.core.utils import V

from .tmpl_support import ObjDict,debugPrintout
from .tmpl_storage import json_to_dataset
 
#================================================================
#%% Constants
#================================================================
 
#================================================================
#%% Decorator Functions
#================================================================
def test_time(func):
    """
    Test time calculator
    decorator function put it above a function like this

    @test_time
    def myfunction(self)

    It will time how long the function takes and display it.
    """                                                                                                   
                                                                                                                          
    def wrapper(self,*arg,**kwargs):                                                                                                      
        t = time.time()            
        self.log('<<'*10)
        res = func(self,*arg,**kwargs)  
        self.test_time_s = time.time()-t                                                                                            
        self.log(">>\tTime taken: %.3fs " % (self.test_time_s))                                                    
        return res    

    # Documentation
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__                                                                                      
    return wrapper

def with_results(func):
    """
    Checks if there are results available to process
    If not then it throws an error

    @with_results
    def myfunction(self)

    """                                                                                                   
                                                                                                                          
    def wrapper(self,*arg,**kwargs):       
        if not hasattr(self,'ds_results'):
            raise ValueError('This object has no "ds_results" property')      

        if self.ds_results is None:
            raise ValueError('No results to process')
        
        res = func(self,*arg,**kwargs)  
                                                          
        return res    

    # Documentation
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__                                                                                      
    return wrapper

def service(func):
    """
    Service decorator
    This will add a tag property to a function called 'is_service' so that
    the function/method can be identified as a service.

    When writing a Measurement class, any method that is to be offered as
    a service can be tagged with the @service decorator
    e.g.

        from tmpl_core import service

        @service
        def my_service(self,args,**kwargs):
            ...

    or 

        import tmpl_core as TMPL

        @TMPL.service
        def my_service(self,args,**kwargs):
            ...

    Parameters
    ----------
    func : function/method reference
        Normal input to decorator

    Returns
    -------
    function/method reference
        Returns same as input except that it adds a new property 
        called 'is_service'

    Adapted from
    https://stackoverflow.com/questions/47559480/is-there-a-way-to-tag-specific-class-methods
    """
    func.is_service = True
    return func




#================================================================
#%% Common utility class
#================================================================
class CommonUtility():
    """
    Common utilities that are used in more than one of the main classes
    in the test_measure_process library.

    """

    # Common run conditions
    RUN_COND_STARTUP = 'startup' # Before all measurements start
    RUN_COND_TEARDOWN = 'teardown' # After all measurement end
    RUN_COND_TEARDOWN_AFTER_CONDITIONS = 'teardown_after_conditions'

    # Offline mode
    offline_mode = False
    """Flag that sets if the object is to be used offline, i.e. no hardware """
    


    #----------------------------------------------------------------
    #%% Resource helpers
    #----------------------------------------------------------------
    def get_resource(self,label):
        """
        Return an element from the self.resources dict
        Helper function
        This will throw an error if the resource is not available
        Intended for use in the initialise() method for extracting resources in
        a single line without having to put in a lot of boiler plate code to
        check if the resource is there and throw an error.

        Example usage

        >>> self.station = self.get_resource('station')

        Parameters
        ----------
        label : str
            label in self.resources to search for

        Returns
        -------
        any
            The corresponding value in self.resources dict

        Raises
        ------
        ValueError
            If the resource is not found
        """
        if self.offline_mode:
            # If offline then resources, e.g. test equipment, may not be
            # available. Don't throw an error because user may just want to
            # use processing functions. Just return None and let it break
            # further on.
            return self.resources.get(label,None)

        if label not in self.resources:
            raise ValueError(f'Measurement [{self.name}] cannot access resource [{label}]')

        return self.resources[label]


    #----------------------------------------------------------------
    #%% Dataset processing methods
    #----------------------------------------------------------------
    # All the core classes have a ds_results property that is used to
    # contain measured data. These methods provide wrappers for entering
    # data into ds_results without having to get too involved with the
    # xarray data set manipulation.

    def clear_results(self):
        """
        Reset all ds_results properties
        """
        self.ds_results = None

    def set_conditions(self,conditions):
        """
        Add conditions into ds_results Dataset
        This is used whenever the run() method is called to add new 
        conditions.

        This is primarily used in classes based on AbstractMeasurement

        Parameters
        ----------
        conditions : dict like
            Dictionary of condition values. The key is the name of the
            condition, corresponding to a coordinate in self.ds_results
            and the value is a single value representing one condition
            e.g. conditions = {'temperature_degC':25,'humidity_pc':50}

        Raises
        ------
        ValueError
            Return error if the condition values are not single valued, e.g. if
            they are lists or arrays.
        """

        # Validate input
        # ==============================
        # Look for lists or arrays, we don't want them
        not_single_value = [key for key in conditions if hasattr(conditions[key],'__len__')]

        if not_single_value!=[]:
            raise ValueError(f'Conditions must be single values. These conditions have multiple values [{not_single_value}]')

        # Add conditions to Dataset
        # ==============================
        # Initialise dataset for these conditions
        ds_new = xr.Dataset()

        # Add the conditions
        for name,value in conditions.items():
            ds_new.coords[name] = [value]

        # If no data make this ds_results
        if self.ds_results is None:
            self.ds_results = ds_new
            return

        # If existing data, merge new dataset into existing
        # - this will increase the size of data variable dimensions
        # and pad with NaNs
        self.ds_results = xr.merge([self.ds_results,ds_new])
        


    def store_data_var(self,name,data_values,coords=[]):
        """
        Store data into a data variable in self.ds_results
        Creates a new data variable or overwrites existing data.
        The new data variable also has all the current conditions appended
        to it.

        Parameters
        ----------
        name : str
            Name of new data variable. No spaces, ascii only
        data_values : list or array
            Array of data to be added to data variable
            The dimensions of the array needs to be consistent with the coordinates
            being requested.

        coords : list or dict, optional
            List of coordinates for this data variable, usually added by
            the store_coords() method,
            e.g. ['sweep_voltage']
            by default []
            Can also be a dict if a specific coordinate value is being
            requested
            e.g. {'trib':'XI'}
            If some coordinates need specific values and others do not then
            they can be mixed in the dict by setting the value to None for those
            that do not have a value
            e.g. {'trib':'XI','sweep_voltage':None}

        Raises
        ------
        
        """

        # Input validation
        # ==============================
        # Convert data to array
        data_values = np.atleast_1d(data_values)

        # Convert coords to dict
        if coords==[]:
            coords = {}

        if isinstance(coords,list):
            coords = {k:None for k in coords}

        # Combine coordinates
        coordinates = copy.deepcopy(self.current_conditions)
        coordinates.update(coords)

        if len(coordinates)==0:
            raise ValueError(f'Data variable being added [{name}] has no coordinates. There are no setup conditions active.')

        # Check all coordinates exist
        missing = [c for c in coordinates if c not in self.ds_results.coords]
        if missing!=[]:
            raise ValueError(f'Trying to add to [{name}] data variable with unknown coordinates {missing}')

        # Processing
        # ==============================
        if name not in self.ds_results:
            # Create new data variable
            # Fill it with NaNs to start
            filler = np.empty(tuple([self.ds_results.coords[c].size for c in coordinates]))*np.nan
            self.ds_results[name] = (list(coordinates.keys()),np.atleast_1d(filler))

            
        # Check input data has the correct shape
        filtered_coords = {k:v for k,v in coordinates.items() if v is not None}
        req_shape = self.ds_results[name].sel(filtered_coords).shape

        # Special case where there is only one element
        # for some reason the dataset data variable returns a shape of ()
        # when there is only one value. This will fail the general case
        # below because the data_values array has a shape of (1,)
        if req_shape==():
            if data_values.size!=1:
                raise ValueError(f'The data array being entered for [{name}] should only have 1 element to satisfy coordinates {coordinates} not [{data_values.shape}]')
            
            self.ds_results[name].loc[filtered_coords] = data_values[0]
            return

        # General case
        # - array has more than one value
        if data_values.shape!=req_shape:
            raise ValueError(f'The data array being entered for [{name}] must have a shape [{req_shape}] to satisfy coordinates {coordinates}')

        # Insert data at selected coordinates
        self.ds_results[name].loc[filtered_coords] = data_values


    def store_coords(self,name,values):
        """
        Add a new coordinate to self.ds_results or overwrite and existing one

        Parameters
        ----------
        name : str
            Name of new coordinate, no spaces, ascii
        values : list or array
            1D list or array of values for this coordinate

        Raises
        ------
        
        """

        if self.ds_results is None:
            self.ds_results = xr.Dataset()

        if name not in self.ds_results:
            self.ds_results.coords[name] = values
            return

        # TODO : Want to make this more flexible and be able to take extra values
        #  and pad with NaNs if necessary

        # Already exist, then check the values are the same
        if len(self.ds_results[name])!=len(values):
            raise ValueError(f'New values for Dataset coordinate [{name}] has different length to existing values')

        if not all(self.ds_results.coords[name]==np.array(values)):
            raise ValueError(f'Dataset coordinate [{name}] has different values than what is being entered')


    #----------------------------------------------------------------
    #%% Dataset saving/loading
    #----------------------------------------------------------------
    def save(self,filename,format='json'):
        """
        Save ds_results dataset

        Parameters
        ----------
        filename : str
            Full path/filename 
        format : str, optional
            File format to save in, by default 'json'
            Options are:
                * 'json'
                * 'excel'   

        Raises
        ------
        ValueError
            If file format is not supported
        """

        if format.lower()=='json':
            self.ds_results.save.to_json(filename)
        elif format.lower()=='excel':
            self.ds_results.save.to_excel(filename)
        else:
            raise ValueError(f'Cannot save in format [{format}]')


    def load(self,filename):

        if not os.path.exists(filename):
            raise FileNotFoundError(f'Cannot find file at [{filename}]')

        if not os.path.splitext(filename)[1].lower()=='.json':
            raise ValueError('Can only load .json files')

        self.ds_results = json_to_dataset(filename)



 
#================================================================
#%% Test Manager Class
#================================================================
class AbstractTestManager(abc.ABC,CommonUtility):
    """
    Test manager class template definition
    Test manager is responsible for running measurements over multiple conditions
    and collecting up all the data.

    Measurements are implemented as class that inherit from AbstractMeasurement.
    Setup conditions are classes based on AbstractSetupConditions.

    Measurements and setup conditions are held in dictionaries that are class
    properties:
        * self.meas : contains all available measurements for this test
        * self.conditions : all conditions classes for this test

    
    """

    name = 'default_test_manager_name'

    def __init__(self,resources={},**kwargs) -> None:

        # Main components
        # ==============================
        # Resources
        self.resources = resources
        
        # Test condition objects
        self.conditions = ObjDict()

        # Test measurement objects
        self.meas = ObjDict()

        # Services
        self.services = ObjDict()

        # Information
        self.information = ObjDict()

        # Utilities
        # ==============================
        # Offline mode
        # - can either be set in kwargs or resources
        #   using resources is a bit of kludge to propagate the 
        #   flag to sub classes
        self.offline_mode = kwargs.get('offline_mode',False)
        self.offline_mode = resources.get('offline_mode',self.offline_mode)
        if self.offline_mode:
            # Store in resources for sub classes
            self.resources['offline_mode'] = self.offline_mode

        # Logging
        self.log = debugPrintout(self)
        self.last_error = ''
        self.log_section_separator = '='*40
        self.log_sub_section_separator = '-'*40

        # Setup conditions and measurement objects
        self.define_setup_conditions()
        self.define_measurements()

        # Scan for services
        self.get_services()

        # Run custom setup
        self.initialise()

        


    def __repr__(self):
        return f'TestManager[{self.name}]'

    #----------------------------------------------------------------
    #%% Run methods
    #----------------------------------------------------------------

    @test_time
    def run(self,conditions=None):
        """
        Run full test over all or specified conditions [Mandatory function]

        Parameters
        ----------
        conditions : list of dict, optional
            list of dict of conditions, by default None
            Conditions are specified as key value pairs
            e.g.
                conditions = [dict(temperature_degC=34,wavelength_nm=1550)]
                conditions = [{'temperature_degC':34,'wavelength_nm':1550}]
                conditions = [{'temperature_degC':40,'wavelength_nm':1550}]
                conditions = [
                    {'temperature_degC':25,'wavelength_nm':1550},
                    {'temperature_degC':40,'wavelength_nm':1560},
                    ]


        Raises
        ------
        ValueError
            If supplied conditions are the wrong format
        """
        # Setup
        # ==============================
        self.clear_all_results()

        # Get conditions
        if not conditions:
            conditions_table = self.conditions_table
        else:
            conditions_table = conditions
            # TODO check over conditions input
        
        if not isinstance(conditions_table,list):
            raise ValueError('Supplied conditions should be a list of dicts with format {cond_name:cond_value}')
    

        # Main sequence
        # ==============================
        self.log(self.log_section_separator)
        self.last_error = ''
        try:

            # Pre-processing
            # ==============================
            self.pre_process()

            # Main measurement loop
            # ==============================

            # Loop through conditions
            for current_cond in self.conditions_table:
                self.log(self.log_section_separator)

                # Setup
                # -----------
                self.run_on_condition(self.RUN_COND_STARTUP,conditions=current_cond)

                # Set conditions
                # ------------------------------
                # Make a dict for keeping track of conditions incrementally
                accum_cond = {}

                # Loop through current set of conditions
                for cond_label in self.conditions:
                    # set individual condtion
                    name = self.conditions[cond_label].name
                    self.conditions[cond_label].setpoint = current_cond[name]

                    # Accumulate conditions for measurements
                    accum_cond[name] = current_cond[name]

                    # Loop through measurements at this condition
                    # - measurements are given the accumulated conditions
                    #   for setting coordinates in their ds_results datasets
                    self.run_on_condition(name,conditions=accum_cond)

                    
                # Main measurements
                # ------------------------------
                # Loop through measurements that don't have a specific 
                # run_condition
                self.run_on_condition('',conditions=current_cond)


                # Teardown after individual conditions
                # -------------------------------------
                self.run_on_condition(self.RUN_COND_TEARDOWN_AFTER_CONDITIONS,conditions=current_cond)


            self.log(self.log_section_separator)

            # Teardown after all measurements are done
            # ======================================
            self.run_on_condition(self.RUN_COND_TEARDOWN_AFTER_CONDITIONS,conditions=current_cond)
            

            # Post processing
            # ==============================
            self.post_process()
            
            
        except Exception as err:
            success = False
            self.last_error = traceback.format_exc()
            print(f'TestManager[{self.name}] has thrown an error')
            print('*'*40)
            traceback.print_exc()
            print('*'*40)

        finally:
            # Grab all results regardless of any errors
            self.get_results()

        self.log(self.log_section_separator)
        if self.last_error!='':
            self.log('Test finished with errors - check last_error property')




    def run_on_condition(self,condition_label,conditions={'default':0}):
        """
        Run only measurements that have the run_condition specified

        Parameters
        ----------
        condition_label : str
            run_condition label of the measurements to be run
            
        conditions : dict, optional
            dict of conditions
            Conditions are specified as key value pairs
            e.g. conditions = {'temperature_degC':34,'wavelength_nm':1550}
        """

        for meas_label in self.meas:
            # Select only measurements whose run_condition 
            # corresponds to condition_label
            if self.meas[meas_label].run_condition!=condition_label:
                    continue

            # Run individual measurement
            # - supply conditions for setting coordinates in ds_results dataset
            ok = self.meas[meas_label].run(conditions=conditions)
            assert ok, f'Measurement [{meas_label}] failed at conditions {conditions}'



    #----------------------------------------------------------------
    #%% Conditions properties/methods
    #----------------------------------------------------------------

    @property
    def conditions_table(self):
        """
        Put all setup conditions into one 'table'
        Convenience function

        The order of the conditions in self.conditions dictates how each condition
        varies. The first condition varies the slowest and the last condition the
        fastest.

        Returns
        -------
        list of dicts
            List of all combinations of the setup conditions held in self.conditions
            Each item is a dict where the key is the name of the condition
            and the value is the setpoint of that condition.
            e.g.
            conditions_table = [
                {'temperature_degC': 1.0, 'humidity_pc': 2.0, 'pressure_Kpa': 3.0},
                {'temperature_degC': 1.0, 'humidity_pc': 2.0, 'pressure_Kpa': 3.1},
                {'temperature_degC': 1.0, 'humidity_pc': 2.0, 'pressure_Kpa': 3.2},
                {'temperature_degC': 1.0, 'humidity_pc': 2.1, 'pressure_Kpa': 3.0},
                :
                {'temperature_degC': 1.2, 'humidity_pc': 2.1, 'pressure_Kpa': 3.2},
                {'temperature_degC': 1.2, 'humidity_pc': 2.2, 'pressure_Kpa': 3.0},
                {'temperature_degC': 1.2, 'humidity_pc': 2.2, 'pressure_Kpa': 3.1},
                {'temperature_degC': 1.2, 'humidity_pc': 2.2, 'pressure_Kpa': 3.2},
            ]
        """

        # Get all conditions into a list of dicts
        cond_labels = [c.name for c in self.conditions.values()]
        cond_values = itertools.product(*[c.values for c in self.conditions.values()])
        cond_table = [{k:v for k,v in zip(cond_labels,m)} for m in cond_values]

        return cond_table

    #----------------------------------------------------------------
    #%% Service handling methods
    #----------------------------------------------------------------
    def get_services_from_object(self,object):
        """
        Scan through the attributes of an object to see if it has any
        services registered.

        Services are identified by the attribute having a property called
        'is_service'. This is added by the @service decorator defined above.

        Attributes identified as services are added to self.services using
        the method name or whatever is in their __name__ property.

        Parameters
        ----------
        object : Measurement or SetupConditions class
            A TMPL object e.g. any class based on AbstractMeasurement or
            AbstractSetupConditions
        """
        methods = inspect.getmembers(object, predicate=inspect.ismethod)
        methods = [m[0] for m in methods if not m[0].startswith('_')]

        # for attr in [a for a in dir(object) if not a.startswith('_')]:
        for attr in methods:
            attr_obj = getattr(object,attr)

            try:

                if hasattr(attr_obj,'is_service'):
                    # print(f'{attr_obj.__name__} : is a service')
                    self.services[attr_obj.__name__] = attr_obj

            except:
                # Ignore failures, which are usually the ObjDict properties
                # print(f'Weird object [{attr}]')
                pass



    def get_services(self):
        """
        Scan defined measurements and conditions objects to find any methods
        that are tagged as services.

        Add any service methods to the self.services property

        Link the services to each measurement and condition object so that
        they will be available to all.
        """

        # Scan for services
        # ==============================
        for meas in self.meas.values():
            self.get_services_from_object(meas)

        for cond in self.conditions.values():
            self.get_services_from_object(cond)

        # Link services to all measurements and conditions
        # ==================================================
        for meas in self.meas.values():
            meas.services = self.services

        for cond in self.conditions.values():
            self.services = self.services


    @property
    def services_available(self):
        """
        List available services

        Returns
        -------
        list of str
            List of the names of the available services
        """
        return list(self.services.keys())


    def is_service_available(self,service_name):
        """
        Check if a service is available

        Parameters
        ----------
        service_name : str
            Name of service

        Returns
        -------
        bool
            True if the named service is available
            False otherwise
        """
        return service_name in self.services
    


    #----------------------------------------------------------------
    #%% Results methods
    #----------------------------------------------------------------
    def clear_all_results(self):
        """
        Reset all results in all measurements and conditions
        """

        # Clear measurement methods
        # ==============================
        for m in self.meas:
            # Deal with no results cases
            if not hasattr(self.meas[m],'ds_results'):
                continue
            self.meas[m].clear_results()

        # Clear conditions
        # ==============================
        for c in self.conditions:
            # Deal with no results cases
            if not hasattr(self.conditions[c],'ds_results'):
                continue
            self.conditions[c].clear_results()



    def get_results(self):
        """
        Get all the individual datasets out of the measurement objects
        and merge them into final results dataset in self.ds_results
        """

        # Gather all individual datasets
        # =================================
        ds_list = []
        for m in self.meas:
            # Deal with no results cases
            if not hasattr(self.meas[m],'ds_results'):
                continue

            if self.meas[m].ds_results is None:
                continue

            if not self.meas[m].enable:
                continue

            # Get results
            ds_list.append(self.meas[m].ds_results)

        # Merge Datasets together
        self.ds_results = xr.merge(ds_list)
        

        # Add information as coordinates or attributes
        # =============================================
        for key,value in self.information.items():
            try:
                # Try to put info in as a coordinate
                self.ds_results.coords[key] = [value]
            except:
                # Otherwise put info in as attribute
                self.ds_results.attrs[key] = [value]


    #----------------------------------------------------------------
    #%% Mandatory methods (Abstract definitions)
    #----------------------------------------------------------------

    @abc.abstractmethod
    def define_setup_conditions(self):
        """
        Define setup condition classes to be used for this test.
        This means populating the _self.conditions_ property.

        Example usage

        ```python
        def define_setup_conditions(self):
            self.condition['temperature_degC'] = TemperatureConditions(self.resources,values=[25,35,45])
            self.condition['humidity_pc'] = HumidityConditions(self.resources,values=[25,35,45])
        ```

        Returns
        -------
        None

        """
        pass

    @abc.abstractmethod
    def define_measurements(self):
        """
        Define measurement classes to be used for this test.
        This means populating the _self.meas_ property.

        Example usage

        ```python
        def define_measurements(self):
            self.meas['SweepVoltage'] = SweepVoltageMeasurement(self.resources)
            self.meas['SweepCurrent'] = SweepCurrentMeasurement(self.resources)
        ```

        Returns
        -------
        None

        """
        pass


    #----------------------------------------------------------------
    #%% Optional methods
    #----------------------------------------------------------------

    def pre_process(self):
        """
        Custom pre processing
        """
        pass

    def post_process(self):
        """
        Custom post processing
        """
        pass

    def initialise(self):
        """
        Custom initialisation/setup
        """
        pass


#================================================================
#%% Measurement class
#================================================================

class AbstractMeasurement(abc.ABC,CommonUtility):
    """
    Measurement class
    This class contains the measurement code. At a minimum it should define the
    'meas_sequence()' method and the 'enable' property.

    Example usage
    -------------
    Create measurement

    >>> meas = MyMeasurement(station,uut)

    Enable/disable measurement

    >>> meas.enable = True # Measurement will run by default
    >>> meas.run()

    >>> meas.enable = False # Measurement will not run 
    >>> meas.run()  # Nothing happends

    Results are returned in an xarray Dataset

    >>> meas.ds_results

    
    """
    name = 'default_measurement_name'


    def __init__(self,resources={},**kwargs):
        """
        Initialise measurement

        Parameters
        ----------
        resources : dict like
            Dictionary like object that contains 'resources'. These can be
            instrument objects, station objects, testboard objects etc.
            The key should be the name of the resource
            e.g. for a station and testboard class
            resources = {'station':station, 'testboard':tb}

            These can be extracted out in the initialise() method, if desired,
            to make them class properties.

        run_condition : str (optional)
            Specifiy the name of the condition where this measurement is run.
            e.g. if the measurement should be run every time the condition
            'temperature' is set then run_condition='temperature'.
            The name must correspond to a key in the TestManager objects
            'conditions' property.

        """
        self.run_condition = kwargs.get('run_condition','')

        # Offline mode
        self.offline_mode = kwargs.get('offline_mode',False)
        self.offline_mode = resources.get('offline_mode',self.offline_mode)

        # Enable/Disable flag
        self.enable =True

        # Dataset initialisation
        self.ds_results = None

        # Storage for current conditions
        self.current_conditions = {}

        # Store the resources
        self.resources = resources

        # Services
        self.services = ObjDict()

        # Configuration data
        self.config = ObjDict()

        # logging
        self.log = debugPrintout(self)
        self.last_error = ''
        self.log_section_separator = '='*40
        self.log_sub_section_separator = '-'*40

        # Run custom initialisation
        self.initialise()
        
        
    def initialise(self):
        """
        Custom initialisation function.
        Put any custom properties and definitions in here. 
        This function will be run automatically when an object is instantiated.

        Example use could be to extract out contents of resources to properties
        e.g.
            self.station = self.resources['station']
            self.tb = self.resources['testboard']
        """
        pass

    @test_time
    def run(self,conditions={'default':0},**kwargs):
        """
        Run measurement sequence at specified conditions 
        This method will run the sequence insided a try/except block to
        catch errors.
        Error messages will be reported in self.last_error

        Parameters
        ----------
        conditions : dict, optional
            Dict of current setup conditions
            Conditions are specified as key value pairs
            e.g.
                conditions = dict(temperature_degC=34,wavelength_nm=1550)
                conditions = {'temperature_degC':34,'wavelength_nm':1550}
               
            The value of each item in the conditions dict is treated as one
            value. The Measurement class does not actually set the conditions
            it just uses them to set coordinates in the ds_results Dataset.

            by default cond = {'default':0}, this allows the measurement to
            be run without specifiying any conditions. All data in self.ds_results
            will have a coordinate called 'default', which can be removed later
            if necessary.

        Returns
        -------
        bool
            True if sequence executed successfully, False if error occurred

        Raises
        ------
        NotImplementedError
            [description]
        """
        # Skip if not enabled
        if not self.enable:
            return True


        # Setup conditions
        # ==============================
        if len(conditions)==0:
            conditions = {'default':0}
            
        self.set_conditions(conditions)
        self.current_conditions = conditions

        # Run measurement sequence
        # ==============================
        success = True
        self.last_error = ''
        try:
            self.meas_sequence(**kwargs)
        except Exception as err:
            success = False
            self.last_error = traceback.format_exc()
            print(f'Measurement[{self.name}] has thrown an error')
            print('*'*40)
            traceback.print_exc()
            print('*'*40)
        
        return success



    @abc.abstractmethod
    def meas_sequence(self):
        """
        Define the sequence of measurements that are executed by the run()
        method.
        This is a mandatory method that all classes must define.
        The user is free to put anything in this method.
        """
        raise NotImplemented('Measurement sequence method not implemented')


    def __repr__(self):
        return f'Measurement[{self.name}]'


    
    
            

#================================================================
#%% Setup conditions class
#================================================================

class AbstractSetupConditions(abc.ABC,CommonUtility):
    """
    Setup conditions class
    This class sets up conditions like temperature, wavelength etc. Conditions
    that are not changing quickly. A measurement will be run under one combination
    of setup conditions.

    Example usage
    -------------
    Create Setup conditions

    >>> cond = MySetupConditions(station,uut,values=[1,2,3])

    Enable/disable conditions

    >>> cond.enable = True # condition will be set by default
    >>> cond.set(value)

    >>> cond.enable = False # Measurement will not run 
    >>> cond.set(value)  # Nothing happends

    State of conditions are returned by

    >>> cond.setpoint
    >>> cond.actual

    Return list of values

    >>> cond.values

    
    """
    name = 'default_condition_name'

    def __init__(self,resources,**kwargs):
        """
        Initialise measurement

        Parameters
        ----------
        station : station class
            Class that contains instrumentation for the station
        uut : any
            Class object that allows measurements of the unit under test

        values : list
            List of allowed values for the setpoints.

        
        """

        # Enable/Disable flag
        self.enable =True

        # Offline mode
        self.offline_mode = kwargs.get('offline_mode',False)
        self.offline_mode = resources.get('offline_mode',self.offline_mode)

        # Station and unit under test objects
        self.resources = resources

        # Condition values
        self.values = kwargs.get('values',[])

        # Services
        self.services = ObjDict()

        # Configuration data
        self.config = ObjDict()

        # logging
        self.log = debugPrintout(self)
        self.last_error = ''
        self.log_section_separator = '='*40
        self.log_sub_section_separator = '-'*40

        # Custom initialisation
        self.initialise()


    def __repr__(self):
        return f'SetupCondition[{self.name}]'

    
    def initialise(self):
        """
        Custom initialisation function.
        Put any custom properties and definitions in here. 
        This function will be run automatically when an object is instantiated.

        Example use could be to extract out contents of resources to properties
        e.g.
            self.station = self.resources['station']
            self.tb = self.resources['testboard']
        """
        pass
        
        
    @property
    @abc.abstractmethod
    def setpoint(self):
        """
        Get/Set the condition setpoint

        e.g.
        >>> cond_temperature_degC.setpoint = 25
        >>> cond_temperature_degC.setpoint
        25

        Raises
        ------
        NotImplementedError
            [description]
        """
        raise NotImplemented('SetupConditions setpoint property not implemented')


    @setpoint.setter
    @abc.abstractmethod
    def setpoint(self,value):
        raise NotImplemented('SetupConditions setpoint property not implemented')



    @property
    @abc.abstractmethod
    def actual(self):
        """
        Get the actual condition value
        Read only value

        e.g.
        >>> cond_temperature_degC.setpoint = 25
        >>> cond_temperature_degC.actual
        25.2

        Raises
        ------
        NotImplementedError
            [description]
        """
        raise NotImplemented('SetupConditions actual property not implemented')


    
    # TODO Entry of list of setpoints

    

    
 
#================================================================
#%% Runner
#================================================================
 
if __name__ == '__main__':
    # Run something
    print('Run')