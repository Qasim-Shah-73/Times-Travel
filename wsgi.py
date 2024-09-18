import sys
import os

# Set the path to your project directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the Flask app object from your run.py file
from run import app as application

# The 'application' object will be picked up by Gunicorn
