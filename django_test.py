#!/usr/bin/env python3
import os
import sys

print("Content-Type: text/html")
print()
print("<h1>Django Test</h1>")

try:
    # Add the project directory to Python path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transcript_project.settings')
    
    # Test Django imports
    print("<p>Testing Django imports...</p>")
    
    import django
    print(f"<p>✓ Django version: {django.get_version()}</p>")
    
    from django.conf import settings
    print(f"<p>✓ Settings loaded: {settings.SETTINGS_MODULE}</p>")
    
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
    print("<p>✓ WSGI application created</p>")
    
    from django.urls import reverse
    print("<p>✓ URL routing available</p>")
    
    print("<h2>✅ Django is working correctly!</h2>")
    print("<p>Your Django application should work now.</p>")
    
except Exception as e:
    print(f"<h2>❌ Django Error</h2>")
    print(f"<p>Error: {str(e)}</p>")
    print(f"<p>Type: {type(e).__name__}</p>")
    import traceback
    print(f"<pre>{traceback.format_exc()}</pre>")
