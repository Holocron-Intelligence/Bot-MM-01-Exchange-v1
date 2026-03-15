import os
import subprocess
import sys

def build():
    """
    Compiles launcher.py into a standalone .exe using Nuitka.
    Ensures assets and config are bundled correctly.
    """
    print("Starting Build Process...")

    # Define paths
    launcher_script = "launcher.py"
    assets_dir = "assets"
    config_dir = "config"
    
    if not os.path.exists(launcher_script):
        print(f"Error: {launcher_script} not found.")
        return

    # Nuitka Command
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",                           # Package everything into a single .exe
        "--windows-disable-console",           # GUI app, no black window
        "--enable-plugin=tk-inter",            # Required for CustomTkinter
        "--include-data-dir=assets=assets",    # Include images
        "--include-data-dir=config=config",    # Include default settings
        "--include-data-dir=src/dashboard/static=src/dashboard/static", # Dashboard HTML/CSS/JS
        "--follow-imports",                    # Ensure all dynamic dependencies are found
        "--output-dir=dist",                   # Output folder
        "--assume-yes-for-downloads",          # Prevent hanging on interactive prompts
        launcher_script
    ]

    print(f"Executing: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "="*50)
        print("BUILD SUCCESSFUL!")
        print("Your executable is in the 'dist' folder.")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"\nBUILD FAILED: {e}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    build()
