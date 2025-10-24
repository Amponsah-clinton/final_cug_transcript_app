#!/usr/bin/env python3
import os
import sys

print("Content-Type: text/html")
print()
print("<h1>Simple Test</h1>")
print("<p>This is a simple Python test for Hostinger.</p>")
print("<p>If you can see this, the basic setup is working.</p>")
print("<p>Current working directory:", os.getcwd())
print("<p>Script location:", __file__)
print("<p>Python executable:", sys.executable)
