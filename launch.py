"""
FCSTN Unified Launcher
Run: python launch.py [command]

Commands:
  demo       Run platform demo (terminal)
  neurogame  Run neurogaming demo with visualizations
  dashboard  Start web dashboard (http://localhost:8000/dashboard)
  test       Run test suite
  present    Open presentation slides
  all        Run everything sequentially
"""

import sys
import os
import subprocess
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent

def cmd_demo():
    os.chdir(ROOT)
    result = subprocess.run([sys.executable, str(ROOT / 'fcstn_platform.py')], capture_output=False)
    sys.exit(result.returncode)

def cmd_neurogame():
    os.chdir(ROOT)
    os.makedirs(ROOT / 'outputs', exist_ok=True)
    result = subprocess.run([sys.executable, str(ROOT / 'neurogaming_demo.py')], capture_output=False)
    sys.exit(result.returncode)

def cmd_dashboard():
    os.chdir(ROOT)
    print("Starting FCSTN Dashboard at http://localhost:8000/dashboard")
    webbrowser.open('http://localhost:8000/dashboard')
    result = subprocess.run([sys.executable, '-m', 'uvicorn', 'src.api.server:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], capture_output=False)
    sys.exit(result.returncode)

def cmd_test():
    os.chdir(ROOT)
    result = subprocess.run([sys.executable, '-m', 'pytest', '-v', '--tb=short'], capture_output=False)
    sys.exit(result.returncode)

def cmd_present():
    path = ROOT / 'docs' / 'presentation.html'
    if path.exists():
        webbrowser.open(f'file://{path.resolve()}')
        print(f"Presentation opened: {path}")
    else:
        print("Presentation not found at docs/presentation.html")

def cmd_all():
    print("=" * 60)
    print("FCSTN - FULL DEMO SEQUENCE")
    print("=" * 60)
    print("\n[1] Running tests...\n")
    subprocess.run([sys.executable, '-m', 'pytest', '-v', '--tb=short', '-m', 'not slow'])
    print("\n[2] Running platform demo...\n")
    cmd_demo()
    print("\n[3] Opening presentation...\n")
    cmd_present()
    print("\n[4] To start dashboard: python launch.py dashboard")

if __name__ == '__main__':
    commands = {
        'demo': cmd_demo,
        'neurogame': cmd_neurogame,
        'dashboard': cmd_dashboard,
        'test': cmd_test,
        'present': cmd_present,
        'all': cmd_all,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(__doc__)
        sys.exit(1)
    commands[sys.argv[1]]()
