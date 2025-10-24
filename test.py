#!/usr/bin/env python3
import os
import sys

print("Content-Type: text/html")
print()
print("<h1>Python is Working!</h1>")
print("<p>If you can see this, Python is properly configured on Hostinger.</p>")
print("<p>Current directory:", os.getcwd())
print("<p>Python version:", sys.version)
print("<p>PATH_INFO:", os.environ.get('PATH_INFO', 'Not set'))
print("<p>REQUEST_URI:", os.environ.get('REQUEST_URI', 'Not set'))
print("<p>SCRIPT_NAME:", os.environ.get('SCRIPT_NAME', 'Not set'))
