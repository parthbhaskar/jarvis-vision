import os
import shutil
import datetime
import subprocess
import psutil
from PIL import ImageGrab
from pycaw.pycaw import AudioUtilities

APPROVED_APPS = {
    "calculator": "calc",
    "calc": "calc",
    "notepad": "notepad",
    "edge": "msedge",
    "browser": "msedge",
    "explorer": "explorer",
    "spotify": "spotify",
    "cmd": "cmd",
    "terminal": "wt"
}

class WindowsController:
    """Hardened Windows 11 System Automation Controller."""

    @staticmethod
    def get_system_status() -> dict:
        """Reads battery, memory, SSD storage, and local time."""
        status = {}

        # 1. Battery Telemetry
        battery = psutil.sensors_battery()
        if battery:
            plugged = "Charging" if battery.power_plugged else "Discharging"
            status["battery"] = f"{battery.percent}% ({plugged})"
        else:
            status["battery"] = "Desktop/AC Power (No battery detected)"

        # 2. Storage & Memory Telemetry
        total, used, free = shutil.disk_usage("C:\\")
        status["free_storage_gb"] = f"{free / (2**30):.1f} GB"
        
        mem = psutil.virtual_memory()
        status["ram_used_percent"] = f"{mem.percent}%"

        # 3. Time
        status["local_time"] = datetime.datetime.now().strftime("%I:%M %p")
        return status

    @staticmethod
    def set_system_volume(level: int) -> str:
        """Sets Windows master volume between 0 and 100."""
        level = max(0, min(100, int(level)))
        try:
            device = AudioUtilities.GetSpeakers()
            # Modern pycaw exposes EndpointVolume directly
            if hasattr(device, "EndpointVolume"):
                volume = device.EndpointVolume
            elif hasattr(device, "Activate"):
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import IAudioEndpointVolume
                interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
            else:
                volume = device.interface

            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Master volume adjusted to {level}%."
        except Exception as e:
            return f"Failed to adjust volume: {e}"

    @staticmethod
    def open_application(app_name: str) -> str:
        """Launches approved Windows applications safely."""
        key = app_name.lower().strip()
        if key in APPROVED_APPS:
            target = APPROVED_APPS[key]
            subprocess.Popen(["cmd", "/c", "start", target], shell=True)
            return f"Successfully launched {app_name}."
        else:
            return f"Access Denied: '{app_name}' is not in the approved applications whitelist."

    @staticmethod
    def capture_screenshot(save_path=None) -> str:
        """Silently captures the primary display without popups."""
        if not save_path:
            save_path = os.path.expanduser("~\\jarvis_screenshot.png")
        screenshot = ImageGrab.grab()
        screenshot.save(save_path, "PNG")
        return save_path

if __name__ == "__main__":
    print("\n--- RE-TESTING VOLUME CONTROLLER ---")
    ctrl = WindowsController()
    print(ctrl.set_system_volume(60))
