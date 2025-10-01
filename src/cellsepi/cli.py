import subprocess
import sys
import platform

def build():
    """
    Build cellsepi with flet build platform -v
    """
    system = platform.system().lower()
    if system == "windows":
        target = "windows"
    elif system == "darwin":
        target = "macos"
    elif system == "linux":
        target = "linux"
    else:
        print("Unknown system")
        sys.exit(1)

    try:
        subprocess.check_call(["flet", "build", target, "-v"])
    except FileNotFoundError:
        print("Flet build failed: Flet not found!")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Flet build failed: {e}")
        sys.exit(1)
