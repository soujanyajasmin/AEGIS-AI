"""
Lifecycle test: Instantiates AegisKivyApp, builds root widget, verifies screens
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_LOG_LEVEL"] = "info"

from kivy_app.app import AegisKivyApp

def test_lifecycle():
    print("[TestLifecycle] Initializing AegisKivyApp...")
    app = AegisKivyApp()
    root = app.build()
    assert root is not None, "Root widget was not created"
    assert app.root_sm.has_screen("login_screen"), "Missing login_screen"
    assert app.root_sm.has_screen("shell_screen"), "Missing shell_screen"

    shell = app.shell_widget
    for sc in ["dashboard", "monitor", "events", "people", "enrollment", "cameras", "storage", "settings"]:
        assert shell.sm.has_screen(sc), f"Missing subscreen {sc}"
        print(f" Verified subscreen: {sc}")

    print("[TestLifecycle] Simulating authenticated user login...")
    app.current_user = {
        "id": 1,
        "username": "admin",
        "role": "admin",
        "full_name": "System Administrator",
        "is_admin": True
    }
    app.on_login_success()
    assert app.root_sm.current == "shell_screen"
    print("[TestLifecycle] Successfully transitioned to authenticated shell!")

    # Verify switching screens
    for sc in ["monitor", "events", "people", "enrollment", "cameras", "storage", "settings", "dashboard"]:
        app.navigate_to(sc)
        assert shell.sm.current == sc
        print(f" Successfully navigated to: {sc}")

    print("[TestLifecycle] Stopping test app...")
    app.on_stop()
    print("[TestLifecycle] SUCCESS: All screens and lifecycle hooks verified cleanly!")

if __name__ == "__main__":
    test_lifecycle()
