# diarization_setup.py
import os
import sys
import ctypes
import subprocess
import argparse
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_diarization_symlinks():
    """Setup required symlinks for diarization with proper error handling"""
    try:
        import torch
        cache_dir = Path.home() / ".cache" / "torch" / "pyannote"
        hub_dir = Path.home() / ".cache" / "torch" / "hub"
        
        # Create directories if they don't exist
        cache_dir.mkdir(parents=True, exist_ok=True)
        hub_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up required symlinks
        links_to_create = [
            (cache_dir, Path.home() / ".cache" / "pyannote"),
            (hub_dir, Path.home() / ".cache" / "hub")
        ]
        
        success = True
        for src, dst in links_to_create:
            try:
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['cmd', '/c', 'mklink', '/D', str(dst), str(src)], 
                                check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"Error creating symlink {dst}: {e.stderr.decode()}")
                success = False
            except Exception as e:
                print(f"Error setting up symlink {dst}: {e}")
                success = False
        
        return success
        
    except Exception as e:
        print(f"Error during diarization setup: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Setup diarization requirements')
    parser.add_argument('--setup', action='store_true', help='Setup diarization symlinks')
    args = parser.parse_args()
    
    if args.setup:
        if not is_admin():
            # Re-run the script with admin privileges
            script = os.path.abspath(sys.argv[0])
            params = ' '.join(sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
            return
        
        success = setup_diarization_symlinks()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()