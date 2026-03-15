import os
import subprocess
import sys

def build():
    print("Starting PyInstaller Build Process...")

    # Define paths
    launcher_script = "launcher.py"
    
    if not os.path.exists(launcher_script):
        print(f"Error: {launcher_script} not found.")
        return

    # PyInstaller Command
    # --onefile: Single EXE
    # --windowed: No console
    # --noconfirm: Overwrite existing dist
    # --add-data: Include folders (format varies by OS, for Windows it's "src;dest")
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--add-data", "assets;assets",
        "--add-data", "config;config",
        "--add-data", "src/dashboard/static;src/dashboard/static",
        "--hidden-import", "tomlkit",
        "--hidden-import", "requests",
        "--hidden-import", "base58",
        "--hidden-import", "aiohttp",
        "--hidden-import", "cryptography",
        "--hidden-import", "pandas",
        "--hidden-import", "numpy",
        "--hidden-import", "customtkinter",
        "--hidden-import", "darkdetect",
        "--collect-all", "customtkinter",
        "--collect-all", "darkdetect",
        "--name", "ZeroOne_Bot_v28",
        launcher_script
    ]

    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print("PYINSTALLER BUILD SUCCESSFUL!")
        print("Your executable is in the 'dist' folder.")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"\nPYINSTALLER BUILD FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
