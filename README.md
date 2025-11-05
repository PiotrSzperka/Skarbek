# Skarbek - szkic aplikacji

Repo szkicuje aplikację Skarbek (FastAPI backend + React frontend). Ten commit zawiera minimalny szkielet.

Jak uruchomić lokalnie (Docker):

```powershell
docker compose build
docker compose up
```

Backend dostępny: http://localhost:8000
Frontend dostępny: http://localhost:3000

Testy backendu (lokalnie, bez Dockera):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```
