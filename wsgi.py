import sys
import os

# Add your project directory to the path
path = '/home/huzaifa7998/Study-Buddy'
if path not in sys.path:
    sys.path.append(path)

# Initialize the database on startup
from app import app, init_db
init_db()

# This is what PythonAnywhere's web server calls
application = app
