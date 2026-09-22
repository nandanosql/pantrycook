# Contributing to PantryCook

Thanks for looking at the project. PantryCook is [Nandan Priyadarshi](https://github.com/nandanosql)'s self-hosted meal app. v0.1 is a single-user server with no authentication.

## Development

1. Fork the repo and create a branch.
2. Backend setup and tests are in the [README](README.md#local-development). From `backend/`:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pytest -q
   ```

3. Frontend: `cd frontend && npm install && npm run dev`.
4. Open a pull request that explains the behaviour change. Include a test when you change matching, scoring, or API contracts.

## Scope

Keep v0.1 focused on pantry, constraints, recipes, and ranked suggestions.

- Do not add accounts, photo upload, or a meal calendar in a drive-by change.
- The matcher must keep working with no API key.
- New copy should sound like PantryCook, not like another product.

## Reporting bugs

Include the request you sent, the response, and whether `OPENAI_API_KEY` was set. Do not paste the key.
