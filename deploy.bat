@echo off
cd frontend
call npm run build
scp -r dist pi@raspberrypi.local:~/stormwater-monitoring-system/frontend/
cd ..