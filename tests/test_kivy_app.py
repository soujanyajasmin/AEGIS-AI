"""
Verification test for Kivy App screens and architecture
"""
import os
import sys

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Ensure headless environment variable for CI/testing if needed
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_LOG_LEVEL"] = "info"

def test_imports():
    print("Testing Kivy imports...")
    import kivy
    from kivy.uix.screenmanager import ScreenManager
    from kivy_app.ui_components import CyberCard, CyberButton, StatCard, StatusBadge, COLORS
    from kivy_app.screens.login import LoginScreen
    from kivy_app.screens.dashboard import DashboardScreen
    from kivy_app.screens.monitor import MonitorScreen
    from kivy_app.screens.events import EventsScreen
    from kivy_app.screens.people import PeopleScreen
    from kivy_app.screens.enrollment import EnrollmentScreen
    from kivy_app.screens.cameras import CamerasScreen
    from kivy_app.screens.storage import StorageScreen
    from kivy_app.screens.settings import SettingsScreen
    from kivy_app.app import MainAppShell, AegisKivyApp
    print("All Kivy app components and screens imported successfully!")

if __name__ == "__main__":
    test_imports()
