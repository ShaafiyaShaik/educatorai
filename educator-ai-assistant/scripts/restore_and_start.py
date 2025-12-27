import shutil, os, subprocess, time
p = os.path.abspath('app/educator_db.sqlite')
recovered = os.path.abspath('recovered_4be3cda3.sqlite')
print('recovered exists:', os.path.exists(recovered))
if os.path.exists(p):
    bak = p + '.bak.' + time.strftime('%Y%m%d%H%M%S')
    shutil.copy2(p, bak)
    print('Backed up', p, '->', bak)
else:
    print('No existing app DB to back up')
shutil.copy2(recovered, p)
print('Restored recovered DB to', p)
# start uvicorn in background
cmd = ['python','-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8003']
print('Starting uvicorn...')
# Start without waiting; on Windows DETACHED_PROCESS flag can be used
DETACHED_PROCESS = 0x00000008
try:
    proc = subprocess.Popen(cmd, creationflags=DETACHED_PROCESS)
    print('Started uvicorn pid', proc.pid)
except Exception as e:
    print('Failed to start uvicorn:', e)
