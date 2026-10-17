# Company Brain - Run Commands

## Terminal 1: Backend
```bash
cd /Users/vulture/GraphHacks
./run_backend.sh
```
- http://localhost:8000 (API)
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/api/health

## Terminal 2: Frontend
```bash
cd /Users/vulture/GraphHacks
./run_frontend.sh
```
- http://localhost:5173 (UI)
- Auto-installs npm deps on first run

## Tests
```bash
cd /Users/vulture/GraphHacks
./run_tests.sh
```
30 passed

## Reset Demo
```bash
cd /Users/vulture/GraphHacks
GRAPH_BACKEND=memory .venv/bin/python scripts/reset_demo.py
```
