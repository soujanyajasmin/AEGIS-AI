"""
AEGIS AI - Desktop Kivy Application Launcher
"""
import sys
import os

# Add root folder to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from kivy_app.app import main

if __name__ == "__main__":
    main()
