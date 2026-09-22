# Getting started

PantryCook v0.1 runs as two containers: the API and the web UI.

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000
- API: http://localhost:8000
- Health: http://localhost:8000/health

The first boot copies `backend/data/seed_recipes.json` into SQLite when the recipe table is empty. Load the sample pantry from the Tonight or Pantry page if you want suggestions immediately.

Leave `OPENAI_API_KEY` empty to stay offline. Set it, and optionally `OPENAI_BASE_URL` and `OPENAI_MODEL`, when you want a short cook tip on suggestions.

v0.1 has no login. Treat the host as private.

More detail lives in the [README](../README.md).
