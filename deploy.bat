@echo off
cd frontend
call npm run build
scp -r dist pi@raspberrypi.local:~/stormwater-monitoring-system/frontend/
cd ..
scp backend\*.py pi@raspberrypi.local:~/stormwater-monitoring-system/backend/
scp backend\routes\*.py pi@raspberrypi.local:~/stormwater-monitoring-system/backend/routes/