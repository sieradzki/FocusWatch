""" This file is used to add the project path to the sys.path list. This is done so that the tests can be run from the root directory of the project. 
"""
import os
import sys

PROJECT_PATH = os.getcwd()
sys.path.append(PROJECT_PATH)
