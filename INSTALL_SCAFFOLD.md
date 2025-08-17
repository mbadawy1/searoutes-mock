# Install the Searoutes Provider Scaffold

## Option A — Quick (Windows PowerShell, merges into your repo)
1. Download `searoutes_provider_scaffold.zip` and move it into your repo folder (the folder that contains your `.git`).
2. Open **PowerShell** in that folder and run:
   ```powershell
   Expand-Archive -Path .\searoutes_provider_scaffold.zip -DestinationPath . -Force
   git add -A
   git commit -m "chore: add Searoutes provider scaffold (milestone 2)"
   git push -u origin HEAD
   ```

## Option B — Manual (VS Code)
1. Open your repo in VS Code (File → Open Folder).
2. Create these files **with the exact paths** and paste the contents from this package:
   - backend/app/providers/base.py
   - backend/app/providers/fixtures.py
   - backend/app/providers/searoutes.py
   - data/fixtures/schedules.sample.json
   - tests/test_providers_contract.py
   - backend/requirements.scaffold.txt (merge entries into backend/requirements.txt)
   - .env.example
3. Commit:
   ```powershell
   git add -A
   git commit -m "chore: add Searoutes provider scaffold (milestone 2)"
   git push -u origin HEAD
   ```

## After installing
- Merge `backend/requirements.scaffold.txt` into your `backend/requirements.txt`.
- Copy `.env.example` to `.env` and set `PROVIDER=fixtures` initially.
- Run tests:
  ```powershell
  pytest -q
  ```
- When ready to go live later, set `PROVIDER=searoutes` and add your `SEAROUTES_API_KEY` in `.env`.
