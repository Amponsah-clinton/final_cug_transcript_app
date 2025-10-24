#!/usr/bin/env python3
import os
import sys
import cgi
import cgitb

# Enable CGI debugging
cgitb.enable()

# Add the parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcript_project.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# CGI handler
def main():
    # Get the path from the URL
    path_info = os.environ.get('PATH_INFO', '/')
    
    # Set up CGI environment
    os.environ['REQUEST_METHOD'] = os.environ.get('REQUEST_METHOD', 'GET')
    os.environ['QUERY_STRING'] = os.environ.get('QUERY_STRING', '')
    
    # Call Django application
    try:
        from django.core.handlers.wsgi import WSGIHandler
        handler = WSGIHandler()
        response = handler.get_response(None)
        
        # Print headers
        print("Content-Type: text/html")
        print("Status: 200 OK")
        print()
        
        # Print response content
        if hasattr(response, 'content'):
            print(response.content.decode('utf-8'))
        else:
            print(str(response))
            
    except Exception as e:
        print("Content-Type: text/html")
        print("Status: 500 Internal Server Error")
        print()
        print(f"<h1>Error: {str(e)}</h1>")

if __name__ == '__main__':
    main()
