import sys
import os
import importlib

# Set the path to your project directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Dynamically import the create_app function from your app module
app_module = importlib.import_module('app')
create_app = getattr(app_module, 'create_app')

# Create an instance of the app with the appropriate config
app = create_app()

# The 'app' object will be picked up by Gunicorn as 'application'
application = app
