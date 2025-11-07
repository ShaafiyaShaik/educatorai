import subprocess
import sys
import os
import time

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    
    # Change to the correct directory
    os.chdir("D:/Projects/agenticai(3)/educator-ai-assistant")
    
    try:
        # Start the server
        process = subprocess.Popen([
            sys.executable, "run_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give it time to start
        time.sleep(3)
        
        # Check if it's running
        if process.poll() is None:
            print("✅ Server started successfully!")
            print("🌐 Server running at: http://localhost:8001")
            print("📝 Use Ctrl+C to stop the server")
            
            try:
                # Keep it running
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                process.terminate()
                
        else:
            print("❌ Server failed to start")
            stdout, stderr = process.communicate()
            if stdout:
                print("STDOUT:", stdout)
            if stderr:
                print("STDERR:", stderr)
                
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_server()