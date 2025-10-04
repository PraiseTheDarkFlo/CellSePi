import os
import shutil
import subprocess
import sys
import platform

def build():
    """
    Build cellsepi with flet build platform -v
    """
    #goto cellsepi folder
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    #check which system is used
    system = platform.system().lower()
    if system == "windows":
        target = "windows"
    elif system == "darwin":
        target = "macos"
    elif system == "linux":
        target = "linux"
    else:
        print("Flet build failed: unknown system")
        sys.exit(1)

    #try to build cellsepi
    try:
        subprocess.check_call([sys.executable, "-m", "flet.cli", "build", target, "-v"])
    except subprocess.CalledProcessError as e:
        print(f"Flet build failed: {e}")
        sys.exit(1)
