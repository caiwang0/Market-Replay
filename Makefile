# Backend port
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

# Frontend port
FRONTEND_PORT=3000

# Directory paths (customize if needed)
BACKEND_DIR=backend
FRONTEND_DIR=frontend

# Commands
FRONTEND_CMD=PORT=$(FRONTEND_PORT) npm run start
BACKEND_CMD=uvicorn app.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

# Backend virtual environment
VENV_DIR=.venv
PYTHON=$(VENV_DIR)/bin/python
UVICORN=$(VENV_DIR)/bin/uvicorn


# === Commands ===
.PHONY: run-be run-fe run stop-be stop-fe logs

## Start Backend
run-be:
	@echo "🚀 Starting Backend..."
	cd backend && . $(VENV_DIR)/bin/activate && $(BACKEND_CMD)

## Start Frontend (uses npm run start)
run-fe:
	@echo "🚀 Starting Frontend..."
	cd $(FRONTEND_DIR) && $(FRONTEND_CMD)

run-dev:
	@echo "Starting frontend and backend..."
	(cd $(FRONTEND_DIR) && npm run dev) & \
	(cd $(BACKEND_DIR) && $(BACKEND_CMD))


## Start both Backend and Frontend in background
run:
	@echo "🚀 Starting BE and FE in background..."
	cd backend && . $(VENV_DIR)/bin/activate && \
	nohup $(BACKEND_CMD) > ../be.log 2>&1 &
	cd $(FRONTEND_DIR) && nohup npm run start > ../fe.log 2>&1 &

## Stop background processes (manual approach)
stop-be:
	pkill -f "uvicorn.*$(BACKEND_APP)"

stop-fe:
	pkill -f "npm run start"

## Tail logs
logs:
	@echo "📝 Backend Logs:"
	@tail -n 20 -f be.log