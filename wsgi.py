#!/usr/bin/env python3
"""
WSGI entry point for production deployment.

This module provides a WSGI application for production deployment using
gunicorn or other WSGI servers.
"""

from web_server import app

if __name__ == "__main__":
    app.run()