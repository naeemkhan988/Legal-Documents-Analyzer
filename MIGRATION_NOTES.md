# FastAPI to Flask Migration Notes

The LegalRAG application has successfully migrated from a split FastAPI/React architecture to a unified, server-rendered Flask monolithic application.

## Key Architectural Changes
1. **Framework Switch:** The backend web framework was swapped from FastAPI to Flask. `backend/main.py` and `backend/api/router.py` were replaced with a traditional Flask App Factory (`backend/__init__.py`).
2. **Routing:** All endpoints were converted to Flask Blueprints (`documents_bp`, `analysis_bp`, etc.).
3. **Database Sessions:** FastAPI's `Depends(get_db)` injection was replaced with a Flask-native pattern. A `SessionLocal()` is now attached to `flask.g.db` during `before_request` and automatically closed during `teardown_appcontext`.
4. **Validation:** Pydantic models are retained but we now explicitly handle request validation and response dumping via `.model_validate()` and `.model_dump()` within each view, rather than relying on framework automation.
5. **Exception Handling:** `HTTPException`s were replaced with a custom `LegalRAGError`, caught by `@app.errorhandler` hooks in the application factory to ensure standardized JSON error responses.

## UI / Frontend
- The separate React SPA was entirely removed.
- Jinja2 templates (located in `backend/templates/`) and minimal vanilla JavaScript (`backend/static/js/`) are now used to render HTML pages directly from the backend via the `pages_bp` blueprint.

## Dependency Swap Decisions
- **Pydantic vs. Marshmallow:** We chose to retain Pydantic (`.model_validate` / `.model_dump`). It required zero changes to our existing schema definitions and integrates easily into Flask views.
- **FastAPI / Uvicorn:** Removed in favor of `flask` and `gunicorn`.
- **CORS:** Swapped to `flask-cors`.

## How to Run the App Locally

### 1. Stopping Old Servers
Ensure that your old `uvicorn` instance is completely stopped. Running both will cause port conflicts and database locks.

### 2. Local Execution (Development)
You can use the built-in Flask development server:
```bash
venv\Scripts\flask.exe --app backend run --port 8000 --debug
```

### 3. Docker Execution (Production)
The `Dockerfile.backend` was updated to use `gunicorn` with multiple workers. To rebuild and run the full stack:
```bash
docker compose up --build -d
```
