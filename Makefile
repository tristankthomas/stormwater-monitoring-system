backend:
	cd backend && uvicorn main:app --reload

frontend:
	cd frontend && npm run dev

deploy:
	cd frontend && npm run build
	scp -r frontend/dist pi@raspberrypi.local:~/stormwater-monitoring-system/frontend/

run-pi:
	cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000