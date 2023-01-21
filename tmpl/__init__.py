"""
Test, Measure, Process Library (TMPL) Main package
================================================================
Import all the main TMPL modules here so that they can be available
from one import

>>> import tmpl

"""
# Version number
__version__ = '1.0.4'

# Imports
from .tmpl_support import *
from .tmpl_storage import *
from .tmpl_core import *
from .tmp_code_generator import make_condition, make_manager, make_measurement, make_module
# from .example_test_setup import *
from .examples import *
