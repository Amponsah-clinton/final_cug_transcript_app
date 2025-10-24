#!/usr/bin/env python3
import os
import sys
import cgi
import cgitb

# Enable CGI debugging for troubleshooting
cgitb.enable()

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcript_project.settings')

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# CGI handler for Hostinger
def main():
    try:
        # Get the path from the URL
        path_info = os.environ.get('PATH_INFO', '/')
        
        # Set up environment variables for Django
        os.environ['REQUEST_METHOD'] = os.environ.get('REQUEST_METHOD', 'GET')
        os.environ['QUERY_STRING'] = os.environ.get('QUERY_STRING', '')
        os.environ['PATH_INFO'] = path_info
        
        # Create a simple WSGI environment
        environ = {
            'REQUEST_METHOD': os.environ.get('REQUEST_METHOD', 'GET'),
            'PATH_INFO': path_info,
            'QUERY_STRING': os.environ.get('QUERY_STRING', ''),
            'CONTENT_TYPE': os.environ.get('CONTENT_TYPE', ''),
            'CONTENT_LENGTH': os.environ.get('CONTENT_LENGTH', ''),
            'SERVER_NAME': os.environ.get('SERVER_NAME', 'localhost'),
            'SERVER_PORT': os.environ.get('SERVER_PORT', '80'),
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https' if os.environ.get('HTTPS') else 'http',
            'wsgi.input': sys.stdin,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Call Django application
        response = application(environ, lambda status, headers: None)
        
        # Print headers
        print("Content-Type: text/html")
        print("Status: 200 OK")
        print()
        
        # Print response content
        for chunk in response:
            if chunk:
                print(chunk.decode('utf-8') if isinstance(chunk, bytes) else str(chunk))
                
    except Exception as e:
        print("Content-Type: text/html")
        print("Status: 500 Internal Server Error")
        print()
        print(f"<h1>Django Error</h1>")
        print(f"<p>Error: {str(e)}</p>")
        print(f"<p>Type: {type(e).__name__}</p>")
        import traceback
        print(f"<pre>{traceback.format_exc()}</pre>")

if __name__ == '__main__':
    main()
