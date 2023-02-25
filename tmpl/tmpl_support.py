#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 13:20:34 2019

@author: jbainbri

Data classes
=================

Useful classes library

"""

#=============================================================================
#%% Imports
#=============================================================================

from collections import OrderedDict
import os
import statistics
import numpy as np

#============================================================================
#%% Functions
#============================================================================

def pad_to_length(string,width,truncate=True,pad_char=' '):
    """
    Pad a string to a given length.
    
    Parameters
    -----------
    string : str
        string to pad
        
    width : int
        number of characters to pad out to
        
    truncate : bool
        If True then the string is truncated if it's too long
        if False then an error is thrown
        
        
    Returns
    --------
    padded_string : str
        the string padded to length
        
    """
    assert len(pad_char)==1, 'Padding character must be length 1'

    # Check length and truncate if necessary    
    if len(string)>width:
        if truncate:
            string = string[0:width]
        else:
            raise RuntimeError('String [%s] is too long for column. Must be less than %i characters' % (string,width))
            
    # Get difference between string length and allowed width
    len_str = len(string)    
    diff = width - len_str
    
    # string length is full width, just return string
    if diff==0:
        return string
    
    # string length is less than full width
    # - work out padding on either side
    if diff % 2 == 1:
        # Odd difference - pad more on left
        left_pad = pad_char*int( (diff-1)/2 + 1)
        right_pad = pad_char*int((diff-1)/2)
    else:
        # even difference - pad equally on both sides
        left_pad = pad_char*int((diff)/2)
        right_pad = pad_char*int((diff)/2)

    return left_pad+string+right_pad


def doc_string_to_text(doc_string):
    """
    Take a python docstring and remove the indent spaces on each line

    Parameters
    ----------
    doc_string : str
        docstring text obtained from object._doc

    Returns
    -------
    list of str
        Reformatted text in list form,
    """
    # Split text into lines
    doc_lines = [l for l in doc_string.split('\n')]

    # Find how many spaces the doc string is indented
    # - compare length of line to stripped length
    indents = [len(l) - len(l.lstrip()) for l in doc_lines if len(l)>1]
    # Assume the most frequently occurring indent is the what we need
    indent = int(statistics.mode(indents))

    # Remove the indents
    text = [l[indent:] for l in doc_lines]

    return text

#=============================================================================
#%% Classes
#=============================================================================

class ObjDict(OrderedDict):
    """
    Dictionary where the keys are also attributes.
    
    This means that the keys can be tab completed.
    
    Examples
    ---------
    
    >>> d = ObjDict()
    
    Use as normal dict
    
    >>> d['p1'] = 1
    >>> d['p1']
    1
    
    Use like an object
    
    >>> d.p2 = 2
    >>> d.p2
    2
        
    Initialise with key/value pairs
    
    >>> d = ObjDict(key1=1,key2=2)
    >>> d.key1
    1
    
    """

    def __init__(self,**kwargs):
        super().__init__()
        
        OrderedDict.__setattr__(self,'key_list', [])
        
        # Add any keyword arguments as key/value pairs
        for k,v in kwargs.items():
            self.__setitem__(k,v)
            

    # Dictionary-like access / updates
    def __setitem__(self, name, value):
        
        # Add to __dir__
        self.key_list.append(name)
        
        super().__setitem__(name,value)
             
    def __dir__(self):
        return self.key_list + super().__dir__()
            

    # Object-like access / updates
    def __getattr__(self, name):
        if name=='__isabstractmethod__':
            return False
        
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value
        self.key_list.append(name)
        
    def __delattr__(self, name):
        self.key_list.pop(name)
        del self[name]   


class debugPrintout:
    """
    Logging printout class
    
    """
    
    # Types of printout
    dbg_levels = ['none','brief','verbose']
    
    def __init__(self,objectInstance = None,level='verbose',class_prefix='@',str_prefix='>'):
        
        # Global verbosity level for this object
        
        self.verbosity_level = level
        self.objectInstance = objectInstance
        self.class_prefix = class_prefix
        self.str_prefix = str_prefix
        
    def __repr__(self):
        """
        Printout
        """
        txt = [
                'debugPrintout(levels=[%s])' % (','.join(self.dbg_levels)),
                'Current level: %s' % self.verbosity_level,
                ]
        return '\n'.join(txt)
    
        
    def __call__(self,message,message_verbosity='verbose'):
        """Print message prepending the calling object
    
        Inputs
        ------
        objectInstance = any object, usually a class or a string
        message :string
            string to be printed
        level : string
            the verbosity level at which this message gets printed, note 
            'verbose' and 'none' will override this.
        
        """
        
        # Check on the global settings
        # ----------------------------------
        if self.verbosity_level == 'none':
            return
            
        if self.verbosity_level == 'verbose':
            message_verbosity = 'verbose'
        
        # Check the level
        # -----------------------
        message_verbosity = message_verbosity.lower()
          
        if message_verbosity != self.verbosity_level:
            return
        
        
        
        
        # Do the printout
        # ----------------------
        if isinstance(self.objectInstance,str):
            caller = self.objectInstance
            printout = self.str_prefix + ' {0:25} | {1:10s}'.format(caller,message)
        else:
            caller = self.objectInstance.__class__.__name__
            printout = self.class_prefix + ' {0:25} | {1:10s}'.format(caller,message)
            
        print(printout)
        
        
    def set_verbosity(self,level):
        """
        Set verbosity level, checking the value is correct
        
        Inputs:
        level: string
            the level of verbosity
            
        """
        assert level in self.dbg_levels, "Unknown Verbosity level %s" % level
        self.verbosity_level = level
        
        
    def get_verbosity(self):
        """
        Return verbosity level
        
        """
        
        return self.verbosity_level
        
    # Make verbosity a property
    verbosity = property(get_verbosity,set_verbosity)
        
# -----------------------------------------------------------------------------
class TablePrinter():
    """
    Class for printing tables
    
    Example usage
    --------------
    Create table class by setting number of columns
    
    >>> table = TablePrinter(['col1','col2','col3'])
    
    Print header
    
    >>> table.header()
    +------+------+------+
    | col1 | col2 | col3 |
    +======+======+======+
    
    Add and print rows
    
    >>> table.addrow([1,2,3])
    | 1    |    2 |    3 |
    +------+------+------+
    >>> table.addrow([10,20,30])
    
    
    The contents of the table is available as a dict, where the keys are
    the names of the columns.
    
    >>> # Get table contents
    >>> table.contents
    {'col1': [1, 10], 'col2': [2, 20], 'col3': [3, 30]}
    
    """

    
    def __init__(self,columns,units=None,formats=None,column_widths=None):
        """
        Create the table object
        
        Parameters
        -----------
        columns : list of str
            List of column names
            
        units : list of str
            List of units for each column. Will be printed below column names
            
        formats : list of str
            List of format strings for each column. Defaults to '%f'
            
        
        """
        
        # List for storing the table
        self.table_list = []
        
        # Dict for storing raw contents of table
        self.contents = {n:[] for n in columns}
        
        # Column names
        self.columns = columns
        self.Ncolumns = len(columns)
        
        # Units
        if units:
            assert len(units)==self.Ncolumns, 'Units list must have the same length as columns [%i]' % self.Ncolumns
            self.units = units
        else:
            self.units = None
        
        # Formats
        if formats:
            assert len(formats)==self.Ncolumns, 'Formats list must have the same length as columns [%i]' % self.Ncolumns
            self.formats = formats
        else:
            self.formats = ['%f']*self.Ncolumns
            
            
            
        # Settings
        # ============
        
        # Maximum width in characters
        self.max_width_char = 120
        
        # Table width as a fraction of total
        self.table_width_percent = 80
            
        # characters used to construct table
        self.char_int = '+'         # Intersection
        self.char_line = '-'        # standard line
        self.char_header_line = '=' # header line
        self.char_vert_sep = '|'    # vertical separator
        
        # Setup
        # ==========
        self.column_widths =[]
        if column_widths:
            assert len(column_widths)==self.Ncolumns, 'Column widths list must have the same length as columns [%i]' % self.Ncolumns
            self.column_widths = column_widths
        
        # Initialise header
        self.make_header()
        
            
    def __repr__(self):
        return 'TablePrinter(%i columns))' % self.Ncolumns
        
    
    @property
    def preferred_width_char(self):
        """
        Return preferred width in characters
        
        """
        return int(self.preferred_width_char*self.max_width_char)
    
            
    def calculate_column_widths(self):
        """
        Calculate column widths
        
        This is used if the column widths have not been specified manually
        
        """
        
        self.column_widths = [len(s) for s in self.columns]
        assert sum(self.column_widths)<self.max_width_char, 'The width of the columns exceeds max of %i characters' % self.max_width_char
        
        
        
        # Check if more width is needed for units
        if self.units:
            for iU,unit_str in enumerate(self.units):
                if (len(unit_str))>self.column_widths[iU]:
                    self.column_widths[iU] = len(unit_str)
               
        self._actual_width = sum(self.column_widths)
        assert self._actual_width<self.max_width_char, 'The width of the units exceeds max of %i characters' % self.max_width_char
            
        # store the difference between max width and required width
        self._excess_width_chars = self.max_width_char - self._actual_width
        
        
        
    
    
    def make_header(self):
        """
        Make column header
        
        Format with no units:
            +------+------+------+
            | col1 | col2 | col3 |
            +======+======+======+
            
        Format with  units:
            +------+------+------+
            | col1 | col2 | col3 |
            |  u1  |  u2  |  u3  |
            +======+======+======+
        
        """
        
        # Check column widths are defined
        # ==================================
        if self.column_widths==[]:
            self.calculate_column_widths()
        
        
        # Make the header
        # ===================
        self._header = []
        
        # Top line
        self._header.append(
                self.char_int 
                + self.char_int.join([self.char_line*n for n in self.column_widths]) 
                + self.char_int)
        
        # Column names
        columns_str = [pad_to_length(u,w) for u,w in zip(self.columns,self.column_widths)]
        self._header.append(
                self.char_vert_sep 
                + self.char_vert_sep.join(columns_str) 
                + self.char_vert_sep)
        
        if self.units:
            units_str = [pad_to_length(u,w) for u,w in zip(self.units,self.column_widths)]
            
            self._header.append(
                self.char_vert_sep 
                + self.char_vert_sep.join(units_str) 
                + self.char_vert_sep)
        
        
        # Bottom line
        self._header.append(self.separator(self.char_header_line))



        
    def header(self):
        """
        Print table header
        
        """
        
        assert hasattr(self,'_header'), 'No table header defined yet'
        assert self._header!=[], 'table header is empty'
        
        print('\n'.join(self._header))
        
        
        
    def addrow(self,row_list,print_row=True):
        """
        Add and print a new row to table
        
        Parameters
        ------------
        row_list : list
            List of values to print in a row
            
        print_row : bool
            True (default) to printout the row immediately
            Otherwise the row is saved
        
        """
        assert len(row_list)==self.Ncolumns, 'Added row does not have enough columns, should be %i' % self.Ncolumns
        
        columns_str = [pad_to_length(f % u,w) for u,w,f in zip(row_list,self.column_widths,self.formats)]
        self.table_list.append(
                self.char_vert_sep 
                + self.char_vert_sep.join(columns_str) 
                + self.char_vert_sep)
        
        # separator line
        self.table_list.append(self.separator(self.char_line))

        
        if print_row:
            print('\n'.join(self.table_list[-2:]))
            
        # Store contents
        for key,value in zip(self.columns,row_list):
            self.contents[key].append(value)
            


    def double_line(self,print_row=True):
        """
        Print double line separator

        Returns
        -------
        None.

        """
        # separator line
        self.table_list.append(self.separator('='))
        self.table_list.append(self.separator(self.char_line))

        
        if print_row:
            print('\n'.join(self.table_list[-2:]))


    def separator(self,line_char='-'):
        """
        Make separator line with specified character

        Parameters
        ----------
        line_char : str, optional
            Character used to print line. The default is '-'.

        Returns
        -------
        line_text: str
            string containing the line text
            

        """
        # separator line

        line_text = (
                self.char_int 
                + self.char_int.join([line_char*n for n in self.column_widths])
                + self.char_int)

        return line_text


    def printout(self):
        """
        Print the whole table
        
        """
        
        self.header()
        print('\n'.join(self.table_list))
        
        
    def dump_string(self):
        """
        Dump the table as a string
        
        Returns
        ---------
        table_str : str
            Table in string form
            
        Example usage
        -------------
        
        >>> print(table.dump_string())
        """
        
        return  '\n'.join(self._header + self.table_list)
        
