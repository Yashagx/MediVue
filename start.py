import subprocess
import time
import os
import sys

# Paths
venv_python = os.path.join("venv", "Scripts", "python.exe")
uvicorn_path = os.path.join("venv", "Scripts", "uvicorn.exe")

# Ensure venv exists
if not os.path.exists(venv_python):
    print("❌ Virtual environment not found. Please set up venv first.")
    sys.exit(1)

def run(cmd):
    return subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)

print("✅ Starting Flask frontend (app.py)...")
flask = run([venv_python, "app.py"])

time.sleep(2)

print("✅ Starting FastAPI backend (app2.py) on port 5001...")
app2 = run([uvicorn_path, "app2:app", "--reload", "--port", "5001"])

time.sleep(2)

print("✅ Starting FastAPI backend (app3.py) on port 5002...")
app3 = run([uvicorn_path, "app3:app", "--reload", "--port", "5002"])

print("\n🚀 All servers are running:")
print("Frontend     → http://127.0.0.1:5000")
print("API - app2   → http://127.0.0.1:5001")
print("API - app3   → http://127.0.0.1:5002")

try:
    flask.wait()
    app2.wait()
    app3.wait()
except KeyboardInterrupt:
    print("\n🛑 Shutting down all servers...")
    flask.terminate()
    app2.terminate()
    app3.terminate()
