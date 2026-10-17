## Company Brain - Correct Commands

### Terminal 1 - Backend API
```bash
cd /Users/vulture/GraphHacks
./run_backend.sh
```
- http://localhost:8000/docs
- http://localhost:8000/api/health

### Terminal 2 - Frontend UI  
```bash
cd /Users/vulture/GraphHacks
./run_frontend.sh
```
- http://localhost:5173

### Tests
```bash
cd /Users/vulture/GraphHacks
./run_tests.sh
```
30 passed

### Reset Demo
```bash
cd /Users/vulture/GraphHacks
GRAPH_BACKEND=memory .venv/bin/python scripts/reset_demo.py
```
