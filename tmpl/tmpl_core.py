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

>>> conditions = dict(temperature_degC=34,humidity=50)
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


from .tmpl_support import ObjDict,debugPrintout
from .tmpl_storage import json_to_dataset
 
#================================================================
#%% Constants
#================================================================
# Operation type labels for the running order
OP_MEAS = 'MEASUREMENT'
OP_COND = 'CONDITION'

# Tags
TAG_CLASSNAME = 'CLASS_TYPE'
 
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
        self.log('<'*40)
        self.log(f'Running {self.name}')

        res = func(self,*arg,**kwargs)  

        self.test_time_s = time.time()-t                                                                                            
        self.log(f"{self.name}\tTime taken: %.3fs " % (self.test_time_s))  
        self.log('>'*40)                                                  
        return res    

    # Documentation
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__                                                                                      
    return wrapper

def with_results(coords=[],data_vars=[]):
    """
    Decorator function
    Checks if there are results available to process
    If not then it throws an error

    Examples
    --------
    Basic check that results exist

    @with_results
    def myfunction(self):
        ...

    Check that specific coordinates and data variable exist

    @with_results(coords=['temperature','pressure'],data_vars=['volume'])
    def myfunction(self):
        ...

    Parameters
    ----------
    coords : list of str
        List of coordinates that must be in ds_results

    data_vars : list of str
        List of data variables that must be in ds_results

    """    

    # Make sure inputs are lists
    if isinstance(coords,str):
        coords = [coords]

    if isinstance(data_vars,str):
        data_vars = [data_vars]

    # Create the decorator function
    def decorator(func):
        """
        Decorator function to be returned

        Parameters
        ----------
        func : function reference
            The actual function to be decorated
        """
        # Wrapper function that does all the work                                                                                                                                # 
        def wrapper(self,*arg,**kwargs):    
            # Check ds_results
            # ==============================   
            if not hasattr(self,'ds_results'):
                raise ValueError('This object has no "ds_results" property')      

            if self.ds_results is None:
                raise ValueError('No results to process')

            missing_coords = [c for c in coords if c not in self.ds_results.coords]
            missing_data_vars = [d for d in data_vars if d not in self.ds_results]

            if missing_data_vars!=[] or missing_coords!=[]:
                raise ValueError(f'Results data is missing coordinates {missing_coords} and data variables {missing_data_vars}')
            
            # Run the actual function
            # ==============================
            res = func(self,*arg,**kwargs)  
                                                            
            return res    

        # Documentation
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__                                                                                      
        return wrapper

    return decorator


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


def with_services(services=[]):
    """
    Decorator function
    Checks if there specific services available
    If not then it throws an error

    Examples
    --------
    Check that specific services exist

    @with_services(services=['read_pressure'])
    def myfunction(self):
        ...
        self.services.read_pressure()


    Parameters
    ----------
    services : list of str
        List of services that must be available


    """    

    # Make sure inputs are lists
    if isinstance(services,str):
        coords = [services]


    # Create the decorator function
    def decorator(func):
        """
        Decorator function to be returned

        Parameters
        ----------
        func : function reference
            The actual function to be decorated
        """
        # Wrapper function that does all the work                                                                                                                                # 
        def wrapper(self,*arg,**kwargs):    
            # Check ds_results
            # ==============================   
            if not hasattr(self,'services'):
                raise ValueError('This object has no "services" property')      

            
            missing_services = [c for c in services if c not in self.services]
    
            if missing_services!=[]:
                raise ValueError(f'Test sequence is missing services: {missing_services}')
            
            # Run the actual function
            # ==============================
            res = func(self,*arg,**kwargs)  
                                                            
            return res    

        # Documentation
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__                                                                                      
        return wrapper

    return decorator


#================================================================
#%% Common utility class
#================================================================
class CommonUtility():
    """
    Common utilities that are used in more than one of the main classes
    in the test_measure_process library.

    """

    
    # Run stages
    # These labels are used to reference all the stages where a measurement
    # can be run
    RUN_STAGE_STARTUP = 'STARTUP'
    RUN_STAGE_TEARDOWN = 'TEARDOWN'
    RUN_STAGE_SETUP = 'SETUP'
    RUN_STAGE_MAIN = 'MAIN'
    RUN_STAGE_AFTER = 'AFTER'
    RUN_STAGE_ERROR = 'ERROR'

    # Offline mode
    offline_mode = False
    """Flag that sets if the object is to be used offline, i.e. no hardware """
    


    #----------------------------------------------------------------
    #%% Resource helpers
    #----------------------------------------------------------------
    def make_resources_into_properties(self,resources):
        """
        Make resources into properties of the class instance
        This is used in __init__() methods so that resources are
        immediately available.

        Parameters
        ----------
        resources : dict
            Dictionary of resources of the format :
                key: resource label
                value: resource object
            Each resource will be made available as a property with
            the name of the key e.g. self.<resource label>
        """

        for label,res in resources.items():
            label_no_spaces = label.strip().replace(' ','_')
            setattr(self,label_no_spaces,res)

            if label!=label_no_spaces:
                print(f'WARNING: resource["{label}"] has spaces in its name, it will appear as property [{label_no_spaces}]')


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
            # Tag with the name of the class
            self.ds_results[name].attrs[TAG_CLASSNAME] = self.__class__.__name__
            
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

        # Special case of 1D vectors
        # The req_shape will be (N,) whereas the data_values shape will be (N,1) 
        # or (1,N). In this case we need to squeeze out the extra dimension
        same_num_elements = np.product(data_values.shape)==np.product(req_shape)
        different_shapes = data_values.shape!=req_shape

        if same_num_elements and different_shapes:
            data_values = data_values.squeeze()

        # Special case of input array dimensions being transposed compared to
        # the equivalent Dataset dimensions
        same_shape_when_transposed = data_values.T.shape == req_shape

        if same_shape_when_transposed:
            data_values = data_values.T

        # General case
        # - array has more than one value
        if data_values.shape!=req_shape:
            raise ValueError(f'The data array being entered for [{name}/{data_values.shape}] must have a shape [{req_shape}] to satisfy coordinates {coordinates}')

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
        """
        Load data into self.ds_results
        If the self object is a measurement or conditions class then it will
        only take data that is usually generated by those classes.

        If the self object is a test manager class it will load the data into
        its self.ds_results property and also distribute the data amongst its
        measurement/conditions classes.

        The net effect should be to recreate all the self.ds_results datasets
        that existed when the file was saved.

        Parameters
        ----------
        filename : str
            full path/filename to data file

        Raises
        ------
        FileNotFoundError
            Data file could not be found
        ValueError
            Data file is not a .json file
        ValueError
            No data for this object could be found in the file
        """

        if not os.path.exists(filename):
            raise FileNotFoundError(f'Cannot find file at [{filename}]')

        if not os.path.splitext(filename)[1].lower()=='.json':
            raise ValueError('Can only load .json files')

        ds = json_to_dataset(filename)

        # Extract subset of data if this object is not a test manager
        if not self.is_test_manager:
            ds_subset = ds.filter_by_attrs(**{TAG_CLASSNAME:self.__class__.__name__})
            if len(ds_subset.data_vars)==0:
                raise ValueError(f'File [{filename}] does not contain any data for {self.__class__.__name__} class')
            self.ds_results = ds_subset
            return

        # Object is Test manager
        # - put all data into self.ds_result, but also distribute to individual
        # measurement/conditions object any data that they usually generate.
        self.ds_results = ds
        self.distribute_loaded_data(ds)


    def distribute_loaded_data(self,ds):
        """
        Distribute data in the test manager ds_results dataset amongst the
        measurement and conditions classes.

        This is usually done when loading data into the test manager object
        from a JSON file. It relies on the data variables in the dataset having
        been tagged by the individual measurement/conditions classes.

        Parameters
        ----------
        ds : xarray Dataset
            Dataset containing data created using the the store_data_var() method
        """

        if not self.is_test_manager:
            return

        # Extract any data for measurement classes
        for meas_obj in self.meas.values():
            ds_subset = ds.filter_by_attrs(**{TAG_CLASSNAME:meas_obj.__class__.__name__})
            if len(ds_subset.data_vars)>0:
                meas_obj.ds_results = ds_subset

        # Extract any data for conditions classes
        for cond_obj in self.conditions.values():
            ds_subset = ds.filter_by_attrs(**{TAG_CLASSNAME:cond_obj.__class__.__name__})
            if len(ds_subset.data_vars)>0:
                cond_obj.ds_results = ds_subset

    #----------------------------------------------------------------
    #%% Config management
    #----------------------------------------------------------------
    def set_custom_config(self,custom_config={}):
        """
        Add custom data to object config dict

        Parameters
        ----------
        custom_config : dict, optional
            Dict-like with custom key,value pairs, by default {}
        """

        # Input validation
        # ==============================
        if not hasattr(self,'config'):
            return

        if custom_config=={}:
            return

        # Write custom values into config ObjDict
        # =========================================
        for key,value in custom_config.items():
            self.config[key] = value


    #----------------------------------------------------------------
    #%% Services
    #----------------------------------------------------------------
    @property
    def services_available(self):
        """
        List available services

        Returns
        -------
        list of str
            List of the names of the available services
        """
        if not hasattr(self,'services'):
            return []

        assert hasattr(self.services,'keys'), 'services property is not dict-like'

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
        if not hasattr(self,'services'):
            return []

        assert hasattr(self.services,'keys'), 'services property is not dict-like'
        
        return service_name in self.services


    #----------------------------------------------------------------
    #%% Identification methods
    #----------------------------------------------------------------
    @property
    def is_test_manager(self):
        """
        Return True if this object is a Test Manager class

        Returns
        -------
        bool
            True : object is a test manager
        """
        # Use python black magic to get the names of the classes
        # that this object is derived from
        base_names = [b.__name__ for b in list(self.__class__.__bases__)]

        # Look for the test manager template
        return 'AbstractTestManager' in base_names


    @property
    def is_measurement_class(self):
        """
        Return True if this object is a Measurement class

        Returns
        -------
        bool
            True : object is a test manager
        """
        # Use python black magic to get the names of the classes
        # that this object is derived from
        base_names = [b.__name__ for b in list(self.__class__.__bases__)]

        # Look for the test manager template
        return 'AbstractMeasurement' in base_names


    @property
    def is_setup_conditions_class(self):
        """
        Return True if this object is a Measurement class

        Returns
        -------
        bool
            True : object is a test manager
        """
        # Use python black magic to get the names of the classes
        # that this object is derived from
        base_names = [b.__name__ for b in list(self.__class__.__bases__)]

        # Look for the test manager template
        return 'AbstractSetupConditions' in base_names



 
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
    name = ''

    def __init__(self,resources={},**kwargs) -> None:
        """
        Initialise test sequence manager object

        Parameters
        ----------
        resources : dict, optional
            Dictionary of objects, e.g. instrument drivers, required by
            the measurements, by default {}

        config : dict, optional
            Configuration settings dictionary. Can be used to store 
            settings and options for measurements. These should be 'standard'
            python variable types, like strings, numbers, lists and dicts
        """

        # Main components
        # ==============================
        # Resources
        self.resources = resources
        self.make_resources_into_properties(resources)

        # Configuration settings
        self.config = ObjDict()
        
        # Test condition objects
        self.conditions = ObjDict()

        # Test measurement objects
        self.meas = ObjDict()

        # Services
        self.services = ObjDict()

        # Information
        self.information = ObjDict()

        # Local data storage
        self.local_data = ObjDict()
        

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
        self.log_condition_separator = '-'*60
        self.log_section_separator = '='*40
        self.log_sub_section_separator = '-'*40

        # Running order
        # Internal list of all the steps in complete test sequence
        self._running_order = []

        # Add in any custom config parameters
        self.set_custom_config(custom_config=kwargs.get('config',{}))

        # Setup conditions and measurement objects
        # =========================================
        self.define_setup_conditions()
        self.define_measurements()

        # Scan for services
        self.get_services()

        # Run custom setup
        self.initialise()

        

        if self.name=='':
            self.name = self.__class__.__name__
        
        


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
                conditions = [dict(temperature_degC=34,humidity=50)]
                conditions = [{'temperature_degC':34,'humidity':50}]
                conditions = [{'temperature_degC':40,'humidity':50}]
                conditions = [
                    {'temperature_degC':25,'humidity':50},
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

        self.make_running_order(conditions)

        if len(self._running_order)==0:
            self.log('Nothing in the running order - aborting')
            return

        # Storage for keeping a log of the current conditions
        current_cond = {label:None for label in self.conditions_table[0]}

        # Main sequence
        # ==============================
        # self.log(self.log_section_separator)
        self.last_error = ''
        try:

            # Startup stage
            # ==============================
            self.pre_process()

            # Main test
            # ==============================
            for line in self._running_order:
                # Set conditions
                if line.operation==OP_COND:
                    print(self.log_condition_separator)
                    self.conditions[line.label].setpoint = line.arguments

                    # Update current conditions log
                    current_cond[line.label] = line.arguments
                
                # Run measurements
                if line.operation==OP_MEAS:
                    ok = self.meas[line.label].run(conditions=line.arguments)
                    assert ok, f'Measurement [{line.label}] failed at conditions {line.arguments}'


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
            print('Running error measurements:')
            self.run_meas_on_error(conditions=current_cond)

        finally:
            # Grab all results regardless of any errors
            self.get_results()

        self.log(self.log_section_separator)
        if self.last_error!='':
            self.log('Test finished with errors - check last_error property')

    
    def make_running_order(self,conditions=None):
        """
        Construct the test sequence running order.
        This creates an internal list (self._running_order) with every step
        in the sequence. The run() method takes this list and executes it 
        line by line.

        This method does the hard work of sorting out the running order leaving
        the run() method with a simpler task.

        To view a tabular version of the running order use the property
        self.df_running_order. This is a pandas DataFrame representation of
        the running order that is easier to read.

        Parameters
        ----------
        conditions : list of dict, optional
            list of dict of conditions, by default None
            Conditions are specified as key value pairs
            e.g.
                conditions = [dict(temperature_degC=34,humidity=50)]
                conditions = [{'temperature_degC':34,'humidity':50}]
                conditions = [{'temperature_degC':40,'humidity':50}]
                conditions = [
                    {'temperature_degC':25,'humidity':50},
                    {'temperature_degC':40,'wavelength_nm':1560},
                    ]


        Raises
        ------
        ValueError
            If supplied conditions are the wrong format
        """
        # Setup
        # ==============================

        # Get conditions
        if not conditions:
            conditions_table = self.conditions_table
        else:
            conditions_table = conditions
            # TODO check over conditions input
        
        if not isinstance(conditions_table,list):
            raise ValueError('Supplied conditions should be a list of dicts with format {cond_name:cond_value}')
    
        self.df_conditions = pd.DataFrame(conditions_table)

        # Clear running order
        self._running_order = []

        self.log('Generating the sequence running order')


        # Startup stage
        # ==============================
        # run startup stage measurements
        self.run_meas_on_startup()


        # Main measurement loop
        # ==============================
        nCond = len(conditions_table)
        self.cond_index = 0

        # Initialise last conditions log
        # - use first column of conditions table to make a template
        last_cond = {label:None for label in self.conditions_table[0]}

        # Loop through conditions
        for self.cond_index,current_cond in enumerate(self.conditions_table):

            # Setup conditions stage
            # ------------------------------
            # Make a dict for keeping track of conditions incrementally
            accum_cond = {}

            # Loop through current set of conditions
            for cond_label in self.conditions:
                # set individual condition
                # - but only if the condition is different
                name = self.conditions[cond_label].name

                # Accumulate conditions for measurements
                accum_cond[name] = current_cond[name]

                # Set condition if it is not the same as the last value
                if current_cond[name]!=last_cond[name]:
                    self.add_to_running_order(OP_COND,cond_label,current_cond[name])
                    # self.conditions[cond_label].setpoint = current_cond[name]

                    # Loop through measurements at this condition
                    # - measurements are given the accumulated conditions
                    #   for setting coordinates in their ds_results datasets
                    self.run_meas_on_setup(name,conditions=accum_cond)

                
            # Main measurements
            # ------------------------------
            # Loop through measurements that don't have a specific 
            # run_condition
            self.run_main_meas(conditions=current_cond)


            # Teardown after individual conditions
            # -------------------------------------
            self.run_after_meas(conditions=current_cond)
            # Store last conditions
            last_cond = current_cond


        # Teardown after all measurements are done
        # ======================================
        self.run_meas_on_teardown()
        
        self.log('\tRunning order done')
            


    def add_to_running_order(self,operation,label,arguments):
        """
        Convenience function for adding a row to the internal running
        order list.
        Checks over the inputs to make sure they work.

        Parameters
        ----------
        operation : str
            String describing type of operation 'MEASUREMENT' or 'CONDITION'
        label : str
            Label of measurement in self.meas or condition in self.conditions
        arguments : single value or dict
            For conditions this is usually a single value for the setpoint
            For measurements this is a dictionary of conditions
        """
        assert operation in [OP_COND,OP_MEAS], f'Running list operation [{operation}] is unknown. Should be [{OP_MEAS},{OP_COND}]'

        if operation==OP_COND:
            assert label in self.conditions, f'Running list: Unknown conditions label [{label}]'
            assert not hasattr(arguments,'__len__'), f'Running list: conditions arguments should be single values not lists [{arguments}]'

        if operation==OP_MEAS:
            assert label in self.meas, f'Running list: Unknown measurement label [{label}]'
            assert hasattr(arguments,'keys'), f'Running list: measurement arguments is not dict-like [{arguments}]'


        self._running_order.append(ObjDict(operation=operation,
                                            label=label,
                                            arguments=copy.deepcopy(arguments)))
        # Note: the deepcopy is needed to stop it storing references that can
        # be updated later in the code

    @property
    def df_running_order(self):
        """
        Return the running order as a pandas DataFrame object
        Useful for displaying the running order in tabular form

        Returns
        -------
        DataFrame
            Table of running order with columns:
            * Operation: either MEASUREMENT or CONDITION
            * Label : label of measurement or condition
            * <condition1> : Value of first condtion
            *     :
            * <conditionN> : Value of last condtion
        """
        # if len(self._running_order)==0:
            # raise ValueError('Running order has not been generated yet. Try make_running_order() method.')
        self.make_running_order()

        rows = []


        for line in self._running_order:
            standard_cols = {'Operation':line.operation,'Label':line.label}
            cond_cols = {k:None for k in self.conditions}

            if line.operation==OP_COND:
                if line.label in cond_cols:
                    cond_cols[line.label] = line.arguments

            if line.operation==OP_MEAS:
                for k,v in line.arguments.items():
                    if k in cond_cols:
                        cond_cols[k] = v

            rows.append(standard_cols | cond_cols)

        return pd.DataFrame(rows)
            


    def run_meas_on_startup(self):
        """
        Add to running order measurements that are done in the startup stage
        This is before any conditions have been set.
        Can be used for turning on instruments, power supplies etc.
        """

        for meas_label in self.meas:
            if self.RUN_STAGE_STARTUP not in self.meas[meas_label].run_conditions:
                # Ignore anything that does not run in this stage
                continue

            self.add_to_running_order(OP_MEAS,meas_label,{})
            
    
    def run_meas_on_teardown(self):
        """
        Add to running order measurements that are done in the teardown stage
        This is before any conditions have been set.
        Can be used for turning off instruments, power supplies etc.
        """

        for meas_label in self.meas:
            if self.RUN_STAGE_TEARDOWN not in self.meas[meas_label].run_conditions:
                # Ignore anything that does not run in this stage
                continue

            self.add_to_running_order(OP_MEAS,meas_label,{})
            

    def run_main_meas(self,conditions={'default':0}):
        """
        Add to running order any measurements that are done in the Main stage
        This is the default mode of operation

        Parameters
        ----------
        conditions : dict, optional
            dict of conditions
            Conditions are specified as key value pairs
            e.g. conditions = {'temperature_degC':34,'humidity':50}

        """

        for meas_label in self.meas:
            if self.RUN_STAGE_MAIN not in self.meas[meas_label].run_conditions:
                # Ignore anything that does not run in this stage
                continue

            self.add_to_running_order(OP_MEAS,meas_label,conditions)
            



    def run_meas_on_setup(self,condition_label,conditions={'default':0}):
        """
        Add to running order measurements at the Setup stage for specified condition
        Measurements are checked to see if they are configured to run for
        the specified condition. If so then they are further checked to see
        for what values of the condition they should be run.

        There are special values
        * meas.COND_FIRST_TIME : run the first time a condition is set to a new value
        * meas.COND_LAST_TIME : run the last time a condition is set to a new value

        Parameters
        ----------
        condition_label : str
            label condition that is currently being set
            
        conditions : dict, optional
            dict of conditions
            Conditions are specified as key value pairs
            e.g. conditions = {'temperature_degC':34,'humidity':50}
        """
        condition_value = conditions[condition_label]

        for meas_label,meas in self.meas.items():
            # Select only measurements whose run_condition 
            # corresponds to the condition stage
            if self.RUN_STAGE_SETUP not in meas.run_conditions:
                    continue

            if condition_label not in meas.run_conditions[self.RUN_STAGE_SETUP]:
                # Ignore measurement if this condition is not specified
                continue

            if condition_value==meas.COND_FIRST_TIME:
                if self.cond_index in self.cond_first_indexes(condition_label):
                    # Skip if this setup index is not the first one
                    continue

            if condition_value==meas.COND_LAST_TIME:
                if self.cond_index in  self.cond_last_indexes(condition_label):
                    # Skip if this setup index is not the first one
                    continue


            # Run individual measurement
            # - supply conditions for setting coordinates in ds_results dataset
            self.add_to_running_order(OP_MEAS,meas_label,conditions)
            

    def run_after_meas(self,conditions={'default':0}):
        """
        Add to running order measurements at the After stage for specified condition
        Measurements are checked to see if they are configured to run for
        the specified condition. If so then they are further checked to see
        for what values of the condition they should be run.

        There are special values
        * meas.COND_FIRST_TIME : run the first time a condition is set to a new value
        * meas.COND_LAST_TIME : run the last time a condition is set to a new value
        

        Parameters
        ----------
        condition_label : str
            label condition that is currently being set
            
        conditions : dict, optional
            dict of conditions
            Conditions are specified as key value pairs
            e.g. conditions = {'temperature_degC':34,'humidity':50}
        """
        

        for meas_label,meas in self.meas.items():
            # Select only measurements whose run_condition 
            # corresponds to the condition stage
            if self.RUN_STAGE_AFTER not in meas.run_conditions:
                    continue

            if not self.check_meas_conditions(meas,self.RUN_STAGE_AFTER,conditions):
                continue

            # Run individual measurement
            # - supply conditions for setting coordinates in ds_results dataset
            self.add_to_running_order(OP_MEAS,meas_label,conditions)
            



    def run_meas_on_error(self,conditions={'default':0}):
        """
        Run any measurements that are done when an error occurs.
        This is useful for safe powering down and cleanup.

        This is the only one of the run_* methods that does not add to
        the running order and actually runs the measurement.

        Parameters
        ----------
        conditions : dict, optional
            dict of conditions
            Conditions are specified as key value pairs
            e.g. conditions = {'temperature_degC':34,'humidity':50}

        """

        for meas_label in self.meas:
            if self.RUN_STAGE_ERROR not in self.meas[meas_label].run_conditions:
                # Ignore anything that does not run in this stage
                continue

            try:
                ok = self.meas[meas_label].run(conditions=conditions)
                assert ok, f'Measurement [{meas_label}] failed at Error stage with conditions {conditions}'
            except Exception as ex:
                self.log(f'Failed to run [{meas_label}] after error')
                self.log(f'Error: [{str(ex)}]')


    #----------------------------------------------------------------
    #%% Condition checking
    #----------------------------------------------------------------
    def check_meas_conditions(self,meas,stage,conditions):
        """
        Check if a measurement object is set to any of the current conditions

        Parameters
        ----------
        meas : Measurement object 
            inherits from AbstractMeasurement

        stage : str
            Label of the sequence stage

        conditions : dict
            dict of current conditions
            Conditions are specified as key value pairs
            e.g. conditions = {'temperature_degC':34,'humidity':50}

        Returns
        -------
        bool
            True if the measurement object is linked to specified conditions
        """
        # Reject anything that is not relevant to this stage
        if stage not in meas.run_conditions:
            return False

        if meas.run_conditions[stage]=={}:
            # Run every time
            # TODO check this works
            return True

        conditions_met = []

        # Extract measurement run conditions
        for condition_label,condition_value in conditions.items():
            conditions_met.append(self.check_single_condition(meas,stage,condition_label,condition_value))

        return any(conditions_met)

    def check_single_condition(self,meas,stage,condition_label,condition_value):
        """
        Check is a single condition is satisfied by a measurement setup
        Return True if any condition is satisfied, otherwise False

        Parameters
        ----------
        meas : Measurement object 
            inherits from AbstractMeasurement
        stage : str
            Label of the sequence stage
        condition_label : str
            Label of condition to be checked
        condition_value : any
            value of condition to be checked

        Returns
        -------
        bool
            True - condition satisfied
            False - condition not satisfied
        """

        # Measurement does not have this condition
        if condition_label not in meas.run_conditions[stage]:
            return False

        # Measurement has this condition and the value is the same
        if meas.run_conditions[stage][condition_label] == condition_value:
            return True

        # Check special values
        if meas.run_conditions[stage][condition_label]==meas.COND_FIRST_TIME:
            if self.cond_index in self.condition_first_indexes(condition_label):
                # index is one of first ones
                return True
                

        if meas.run_conditions[stage][condition_label]==meas.COND_LAST_TIME:
            if self.cond_index in  self.condition_last_indexes(condition_label):
                # index is the last ones
                return True

        return False
                


    def condition_last_indexes(self,cond_label):
        """
        Get the index of the last rows of the condition table where a specific
        condition is set.

        Parameters
        ----------
        cond_label : str
            Label of condtion to return indexes on

        Returns
        -------
        indexes
            list of int, indexes of the last setting of the specified condition
        """

        assert hasattr(self,'df_conditions'),'No attribute "df_conditions"'
        assert cond_label in self.df_conditions.columns, f'df_conditions has no colum [{cond_label}]'

        ind = []
        for label,group in self.df_conditions.groupby(cond_label):
            ind.append(group.index[-1])

        return ind


    def condition_first_indexes(self,cond_label):
        """
        Get the index of the first rows of the condition table where a specific
        condition is set.

        Parameters
        ----------
        cond_label : str
            Label of condtion to return indexes on

        Returns
        -------
        indexes
            list of int, indexes of the first setting of the specified condition
        """

        assert hasattr(self,'df_conditions'),'No attribute "df_conditions"'
        assert cond_label in self.df_conditions.columns, f'df_conditions has no colum [{cond_label}]'

        ind = []
        for label,group in self.df_conditions.groupby(cond_label):
            ind.append(group.index[0])

        return ind


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

    def add_setup_condition(self,cond_class,cond_name=''):
        """
        Add setup conditions 
        This takes a class (not an instance) and creates an instance from it
        that is populated with resources

        Examples
        --------
        class Temperature():
            ...

        testseq.add_condition(Temperature)

        Parameters
        ----------
        cond_class : class reference
            Reference to the class i.e. the class name in code

        cond_name : str
            Name to be used to reference setup condition. This will appear
            as a key in the self.conditions dict and also as a coordinate
            in ds_results.
            If nothing is specified then the class name is used.
        """
        if cond_name=='':
            if cond_class.name == '':
                cond_name = cond_class.__name__
            else:
                cond_name = cond_class.name

        self.conditions[cond_name]= cond_class(self.resources,config=self.config)


    #----------------------------------------------------------------
    #%% Measurement methods
    #----------------------------------------------------------------
    def add_measurement(self,meas_class,meas_name=''):
        """
        Add measurement class
        This takes a class (not an instance) and creates an instance from it
        that is populated with resources

        Examples
        --------
        class VoltageSweep():
            ...

        testseq.add_measurement(VoltageSweep)

        Parameters
        ----------
        meas_class : class reference
            Reference to the class i.e. the class name in code

        meas_name : str
            Name to be used to reference measuremEnt. This will appear
            as a key in the self.meas dict.
            If nothing is specified then the class name is used.
        """
        if meas_name=='':
            if meas_class.name == '':
                meas_name = meas_class.__name__
            else:
                meas_name = meas_class.name

        self.meas[meas_name] = meas_class(self.resources,config=self.config)


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

    >>> meas = MyMeasurement(resources)

    Enable/disable measurement

    >>> meas.enable = True # Measurement will run by default
    >>> meas.run()

    >>> meas.enable = False # Measurement will not run 
    >>> meas.run()  # Nothing happends

    Results are returned in an xarray Dataset

    >>> meas.ds_results

    
    """
    name = ''

    # Special conditions
    COND_EACH = 'EACH'
    COND_FIRST_TIME = 'FIRST_TIME'
    COND_LAST_TIME = 'LAST_TIME'


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
        # TODO may deprecate this
        self.run_condition = kwargs.get('run_condition','')

        # Dict to hold conditions when this is run
        self.run_conditions = {}

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
        self.make_resources_into_properties(resources)

        # Services
        self.services = ObjDict()

        # Configuration data
        self.config = ObjDict()

        # Local data storage
        self.local_data = ObjDict()

        # logging
        self.log = debugPrintout(self)
        self.last_error = ''
        self.log_section_separator = '='*40
        self.log_sub_section_separator = '-'*40

        # Default run conditon
        # - run in main block
        # - If any other condition is chosen
        self.run_on_main(True)

        # Run custom initialisation
        self.initialise()

        # Add in any custom config parameters
        self.set_custom_config(custom_config=kwargs.get('config',{}))

        if self.name=='':
            self.name = self.__class__.__name__
        
        
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
        This method will run the sequence inside a try/except block to
        catch errors.
        Error messages will be reported in self.last_error

        Parameters
        ----------
        conditions : dict, optional
            Dict of current setup conditions
            Conditions are specified as key value pairs
            e.g.
                conditions = dict(temperature_degC=34,humidity=50)
                conditions = {'temperature_degC':34,'humidity':50}
               
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
            print(f'Measurement sequence for[{self.name}] has thrown an error')
            print('*'*40)
            traceback.print_exc()
            print('*'*40)
        
        # Failed on running sequence, exit cleanly
        if not success:
            return success

        # Run processing
        # ==============================
        self.last_error = ''
        try:
            self.process()
        except Exception as err:
            success = False
            self.last_error = traceback.format_exc()
            print(f'Measurement processing for[{self.name}] has thrown an error')
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


    def process(self):
        """
        Optional processing method. If this function exists it will be
        run after meas_sequence().
        """
        pass


    def __repr__(self):
        return f'Measurement[{self.name}]'


    @property
    def current_results(self):
        """
        Return a subset of ds_results corresponding to the current
        conditions

        Returns
        -------
        xarray Dataset
            Subset of ds_results if there are current conditions populated
            or the whole of ds_results if not
        """
        if self.current_conditions=={}:
            return self.ds_results

        return self.ds_results.sel(self.current_conditions)



    #----------------------------------------------------------------
    #%% Run conditions
    #----------------------------------------------------------------
    # These methods are used to define when a measurement runs in the 
    # main sequence. They are generally called in the initialise() method.
    # All the methods here populate the self.run_conditions dictionary.
    # This gets used by the TestManager class to determine when to run
    # each measurement.

    def run_on_startup(self,enable):
        """
        Set Measurement to run in the Startup stage of the test sequence

        Parameters
        ----------
        enable : bool
            True - enable Measurement condition
            False - remove Measurement condition
        """
        # Add key for startup stage
        # no value required for this
        if enable:
            self.run_conditions[self.RUN_STAGE_STARTUP] = {}
            # Disable main by default
            self.run_on_main(False)
        else:
            if self.RUN_STAGE_STARTUP in self.run_conditions:
                self.run_conditions.pop(self.RUN_STAGE_STARTUP)

    def run_on_teardown(self,enable):
        """
        Set Measurement to run in the Teardown stage of the test sequence

        Parameters
        ----------
        enable : bool
            True - enable Measurement condition
            False - remove Measurement condition
        """
        # Add key for teardown stage
        # no value required for this
        if enable:
            self.run_conditions[self.RUN_STAGE_TEARDOWN] = {}
            # Disable main by default
            self.run_on_main(False)
        else:
            if self.RUN_STAGE_TEARDOWN in self.run_conditions:
                self.run_conditions.pop(self.RUN_STAGE_TEARDOWN)


    def run_on_main(self,enable):
        """
        Set Measurement to run in the Main stage of the test sequence

        Parameters
        ----------
        enable : bool
            True - enable Measurement condition
            False - remove Measurement condition
        """
        # Add key for main stage
        # no value required for this
        if enable:
            self.run_conditions[self.RUN_STAGE_MAIN] = {}
        else:
            if self.RUN_STAGE_MAIN in self.run_conditions:
                self.run_conditions.pop(self.RUN_STAGE_MAIN)


    def run_on_setup(self,condition_label,value=None):
        """
        Run measurement on specific condition during the Setup stage
        This will cause the Measurement to run after that condition has been
        set and before the next is set.

        Parameters
        ----------
        condition_label : str
            Text label of condition that acts as the trigger to run
        value : any, optional
            Condition value to run on, by default None
            If None then the measurement will run every time the condition is
            changed.
            A specific value will cause the measurement to run only when that
            value is set.
            There are also some special values that are encoded in these class 
            properties;
            * self.COND_FIRST_TIME : Run the first time a condition value is changed
            * self.COND_LAST_TIME : Run the last time a condition is set

            These last two apply to the situation where one condition is 
            repeatedly set. For example if the conditions are temperature and 
            humidity and the table of conditions looks like this:

            temperature | humidity
            ------------|----------
            10          |  40        (FIRST_TIME)
            ------------|----------
            10          |  50
            ------------|----------
            10          |  60        (LAST_TIME)
            ------------|----------
            20          |  40        (FIRST_TIME)
            ------------|----------
            20          |  50
            ------------|----------
            20          |  60        (LAST_TIME)
            ------------|----------

            Temperature is set to the same value for 3 rows of the conditions 
            table, we may not want to run a Measurement for each row. Instead we
            may want to run the first time the temperature is set or the last time.
            This is what the FIRST_TIME & LAST_TIME special values are for.
        """
        if self.RUN_STAGE_SETUP not in self.run_conditions:
            self.run_conditions[self.RUN_STAGE_SETUP] = {condition_label:value}
            # Disable main by default
            self.run_on_main(False)
        else:
            self.run_conditions[self.RUN_STAGE_SETUP][condition_label] = value


    def run_after(self,condition_label,value=None):
        """
        Run measurement on specific condition during the After stage.
        The After stage is a cleanup stage after a single set of conditions
        has been run.

        Parameters
        ----------
        condition_label : str
            Text label of condition that acts as the trigger to run
        value : any, optional
            Condition value to run on, by default None
            If None then the measurement will run every time the condition is
            changed.
            A specific value will cause the measurement to run only when that
            value is set.
            There are also some special values that are encoded in these class 
            properties;
            * self.COND_FIRST_TIME : Run the first time a condition value is changed
            * self.COND_LAST_TIME : Run the last time a condition is set

            These last two apply to the situation where one condition is 
            repeatedly set. For example if the conditions are temperature and 
            humidity and the table of conditions looks like this:

            temperature | humidity
            ------------|----------
            10          |  40        (FIRST_TIME)
            ------------|----------
            10          |  50
            ------------|----------
            10          |  60        (LAST_TIME)
            ------------|----------
            20          |  40        (FIRST_TIME)
            ------------|----------
            20          |  50
            ------------|----------
            20          |  60        (LAST_TIME)
            ------------|----------

            Temperature is set to the same value for 3 rows of the conditions 
            table, we may not want to run a Measurement for each row. Instead we
            may want to run the first time the temperature is set or the last time.
            This is what the FIRST_TIME & LAST_TIME special values are for.
        """
        if self.RUN_STAGE_AFTER not in self.run_conditions:
            self.run_conditions[self.RUN_STAGE_AFTER] = {condition_label:value}
            # Disable main by default
            self.run_on_main(False)
        else:
            self.run_conditions[self.RUN_STAGE_AFTER][condition_label] = value



    def run_on_error(self):
        """
        Set entry in run condition to run this measurement when an error occurs
        """
        self.run_conditions[self.RUN_STAGE_ERROR] = {}
    
    
            

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
    name = ''

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

        # Store resources
        self.resources = resources
        self.make_resources_into_properties(resources)

        # Condition values
        self.values = kwargs.get('values',[])

        # Services
        self.services = ObjDict()

        # Configuration settings
        self.config = ObjDict()

        # Local data storage
        self.local_data = ObjDict()

        # logging
        self.log = debugPrintout(self)
        self.last_error = ''
        self.log_section_separator = '='*40
        self.log_sub_section_separator = '-'*40

        # Custom initialisation
        self.initialise()

        # Add in any custom config parameters
        self.set_custom_config(kwargs.get('config',{}))

        if self.name=='':
            self.name = self.__class__.__name__
        


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