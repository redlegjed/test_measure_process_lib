'''
Storage functions for Test Measure Process Library (TMPL)
================================================================
This module defines a class that gets bolted onto xarray datasets
to provide storage methods.
'''
 
 
#================================================================
#%% Imports
#================================================================
# Standard library
import os, time
import json
 
# Third party libraries
import numpy as np
import pandas as pd
import xarray as xr
 
#================================================================
#%% Constants
#================================================================
 
#================================================================
#%% Functions
#================================================================
def dataset_to_json_str(ds):
    """
    Store xarray dataset to JSON string

    Parameters
    ------------

    ds : xarray Dataset
        Dataset to store

    Returns
    -------

    json string

    Example
    --------

    >>> dataset_to_json_str(ds)

    """

    # Convert Dataset to dict
    json_dict = ds.to_dict()

    # Return the json string of dict
    return json.dumps(json_dict)


def dataset_to_json(filename, ds):
    """
    Store xarray dataset to JSON file

    Parameters
    ------------
    filename : str
        Full path/filename

    ds : xarray Dataset
        Dataset to store

    Example
    --------

    >>> dataset_to_json(filename,ds)

    """
    # Convert Dataset to dict, then store dict in JSON file
    json_dict = ds.to_dict()

    with open(filename, "w") as write_file:
        json.dump(json_dict, write_file,indent=4)

# -----------------------------------------------------------------------------
def json_to_dataset(filename,field=None):
    """
    Load xarray dataset that has been stored as a JSON file and convert
    back to a dataset

    Parameters
    ------------
    filename : str
        Full path/filename

    field : str
        optional string giving the field in the JSON file that is a Dataset

    Returns
    --------
    ds : xarray Dataset

    """

    # Validate filename
    # ====================
    assert os.path.exists(filename), 'Cannot find results file [%s]' % filename

    json_dict = None

    # Read file
    # =============
    with open(filename, "r") as read_file:
        json_dict = json.load(read_file)

    try:
        if field:
            ds = xr.Dataset.from_dict(json_dict[field])
        else:
            ds = xr.Dataset.from_dict(json_dict)
    except:
        raise RuntimeError('Cannot load data from [%s]' % filename)

    return ds
 
#================================================================
#%% Classes
#================================================================
@xr.register_dataset_accessor('save')
class StorageAccessor:
    """
    Extension class for xarray dataset to add save functions
    Adds the .save property to datasets.

    Example use
    -----------
    Save to JSON format
    >>> ds.save.to_json(filename)
    
    """

    # Constructor
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

        
    def to_json(self,filename):
        """
        Store dataset to JSON file.

        Parameters
        ----------
        filename : str
            Path to file.

        Returns
        -------
        None.

        """

        dataset_to_json(filename,self._obj)



    def to_json_str(self):
        """
        Store dataset to JSON string.

        Parameters
        ----------
        None

        Returns
        -------

        JSON string.

        """

        return dataset_to_json_str(self._obj)


    def to_excel(self,filename):
        """
        Save dataset to excel file
        Saves each data variable to separate sheet

        Parameters
        ----------
        filename : str
            full path/filename to file location
        """
        if not os.path.exists(os.path.dirname(filename)):
            raise ValueError(f'Path does not exist [{filename}]')

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            for name,da in self._obj.data_vars.items():
                df = da.to_dataframe()

                # Write each data variable to a different worksheet.
                df.to_excel(writer, sheet_name=name)
        

        

 
#================================================================
#%% Runner
#================================================================
 
