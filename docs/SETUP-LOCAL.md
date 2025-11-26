## Szybkie uruchomienie i rozwój lokalny

Poniżej znajdziesz skróconą instrukcję gdzie są istotne pliki, jak lokalnie zbudować i uruchomić aplikację, oraz jak uruchomić testy.

**Struktura (skrót):**
- `backend/` : FastAPI (Python). Kluczowe pliki: `Dockerfile`, `requirements.txt`, `run_migrations.py`, `app/` (kod).
- `frontend/` : React + Vite. Kluczowe pliki: `package.json`, `src/`, testy Playwright.
- `docker-compose.yml` : lokalny skład usług (db, backend, frontend).
- `deploy/proxmox/` : przykładowy compose do produkcji z `BACKEND_IMAGE` i `FRONTEND_IMAGE`.
- `docs/` : dokumentacja projektu.

1) Uruchomienie całości przez Docker Compose

W katalogu root projektu uruchom:

```bash
docker-compose up --build
```

Po chwili usługi będą dostępne pod:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

2) Backend - uruchomienie lokalne bez Dockera

W katalogu `backend`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# opcjonalnie uruchom migracje lokalnie
python run_migrations.py
# uruchom serwer
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Ustaw zmienną środowiskową `DATABASE_URL` gdy chcesz użyć innego DB (np. PostgreSQL):
```
export DATABASE_URL='postgresql+psycopg2://user:pass@host:5432/dbname'
```

3) Frontend - uruchomienie deweloperskie

W katalogu `frontend`:

```bash
npm install
npm run dev
```

Budowa produkcyjna:
```bash
npm run build
npm run preview
```

4) Testy

- Backend (pytest):

  W katalogu `backend` uruchom:

  ```bash
  pytest -q
  ```

  Uwaga: testy backendowe używają sqlite (fixture `conftest.py`) więc nie wymagają zewnętrznego Postgresa.

- Frontend (Playwright e2e):

  W katalogu `frontend`:

  ```bash
  npm install
  npx playwright install
  npx playwright test
  ```

5) Migracje

- Migration runner: `backend/run_migrations.py` wykonuje skrypty SQL z katalogu `backend/migrations` i zapisuje wynik w tabeli `schema_migrations`.
- W środowisku Docker Compose `DATABASE_URL` dla backendu ustawiony jest jako `postgresql+psycopg2://...` — `run_migrations.py` bez problemu konwertuje ten URL do formatu zrozumiałego przez `psycopg2`.

6) Deployment (przykład)

- W katalogu `deploy/proxmox` znajdziesz przykładowy `docker-compose.yml` oraz `.env.example`.
- W trybie produkcyjnym powinieneś zbudować i wypchnąć obrazy Dockera, a następnie w `deploy` ustawić zmienne: `BACKEND_IMAGE`, `FRONTEND_IMAGE`, `POSTGRES_*`, `ADMIN_USER`, `ADMIN_PASSWORD`, `JWT_SECRET`.

7) Uwagi bezpieczeństwa i projektowe

- JWT secret: w produkcji ustaw silny sekret w `JWT_SECRET` — nie używaj domyślnych wartości.
- Zgodnie z zasadami projektu, w payloadach należy używać pola `password` (nie `temporary_password`).
- W CI/CD: push obrazów Docker powinien odbywać się tylko na bezpośrednim `push` do `main`, nie w PR (patrz wewnętrzne wytyczne projektu).

8) Wymuszona zmiana hasła rodzica (feature)

- Modele i endpointy obsługujące flow znajdują się w `backend/app/models.py` i `backend/app/api/parents.py`.
- Kluczowe zachowania:
  - Nowo utworzeni rodzice mają `force_password_change=True`.
  - `POST /api/parents/login` zwraca `require_password_change: True` gdy konieczna jest zmiana.
  - `POST /api/parents/change-password-initial` oczekuje pól `old_password` i `new_password`, resetuje flagę i zwraca nowy token.

Jeśli chcesz, mogę wygenerować prosty `README` w root lub dodatkowy workflow CI przykładowy do GitHub Actions — powiedz co wolisz.
