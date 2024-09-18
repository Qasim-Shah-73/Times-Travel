import sys
import os

# Set the path to your project directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the create_app function from your app
from app import create_app

# Create an instance of the app with the appropriate config
app = create_app()

# The 'app' object will be picked up by Gunicorn as 'application'
application = app
