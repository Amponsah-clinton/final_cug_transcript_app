#!/usr/bin/env python3
import os
import sys

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcript_project.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Simple CGI handler
print("Content-Type: text/html")
print()
print("<h1>Django App is Working!</h1>")
print("<p>If you can see this, the Python setup is working.</p>")
print("<p>Now let's test Django...</p>")

try:
    # Test Django
    from django.core.handlers.wsgi import WSGIHandler
    handler = WSGIHandler()
    print("<p>Django handler created successfully!</p>")
    
    # Try to get a simple response
    from django.http import HttpResponse
    response = HttpResponse("<h1>Django is working!</h1><p>Your app is ready!</p>")
    print(response.content.decode('utf-8'))
    
except Exception as e:
    print(f"<h2>Error: {str(e)}</h2>")
    print("<p>Check your Django settings and file structure.</p>")
