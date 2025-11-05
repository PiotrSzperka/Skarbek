# Plan aplikacji: Skarbek szkolny (FastAPI + React + PostgreSQL)

Krótki opis: Aplikacja webowa dla skarbnika szkolnego, w której rodzice mogą zobaczyć, na co zbierane są pieniądze, oraz sprawdzić, czy zapłacili. Skarbnik ma panel administracyjny do tworzenia zbiórek i oznaczania wpłat. Aplikacja będzie uruchamiana w Dockerze. CI/CD pominięte na tym etapie.

## Checklist (wymagania)

- [x] Rodzice mogą zobaczyć listę zbiórek.
- [x] Rodzice mogą sprawdzić, czy już zapłacili (status indywidualny).
- [x] Panel administracyjny dla skarbnika: tworzenie zbiórek, oznaczanie wpłat.
- [x] Aplikacja konteneryzowana (Docker + docker-compose).

## Kontrakt (wejścia/wyjścia, sukces, błędy)

- Wejście: żądania HTTP/JSON (publiczne i autoryzowane dla admina).
- Wyjście: JSON dla API; responsywny frontend React.
- Błędy: 400 (walidacja), 401/403 (auth), 404 (brak zasobu), 500 (serwer).

## Wybrany stack

- Backend: FastAPI (Python) + Uvicorn
- Baza danych: PostgreSQL
- Frontend: React (Vite)
- Autoryzacja admina: JWT + bezpieczne hasła (bcrypt)
- Kontenery: Docker + docker-compose

## Architektura i struktura katalogów (proponowana)

- backend/
  - app/main.py (FastAPI)
  - app/api/ (routery)
  - app/models/ (SQLAlchemy models)
  - app/schemas/ (Pydantic)
  - app/crud/
  - alembic/ (migracje)
  - requirements.txt / pyproject.toml
- frontend/
  - src/ (React + Vite)
  - pages: Home, Campaign, Admin
- infra/
  - docker-compose.yml
  - Dockerfile.backend
  - Dockerfile.frontend

## Model danych (propozycja tabel SQL)

- campaigns
  - id (PK), title, description, target_amount, created_at, due_date, active
- parents
  - id (PK), name, email, pupil_id, created_at
- contributions
  - id (PK), campaign_id (FK), parent_id (FK), amount_expected, amount_paid, status (pending/partial/paid), paid_at, note
- admin_users
  - id (PK), username, password_hash, role, created_at

## API (przykładowe endpointy)

- Publiczne
  - GET /api/campaigns -> lista zbiórek (id,title,short_desc,target, collected, active)
  - GET /api/campaigns/{id} -> szczegóły zbiórki + suma zebrana
  - GET /api/campaigns/{id}/status?email={email}|pupilId={id} -> status rodzica dla danej zbiórki
- Admin (JWT)
  - POST /api/admin/login {username,password} -> {token}
  - POST /api/admin/campaigns -> utwórz zbiórkę
  - PUT /api/admin/campaigns/{id} -> edytuj
  - GET /api/admin/campaigns/{id}/contributions -> lista wpłat/przypisanych rodziców
  - POST /api/admin/contributions/mark-paid {campaign_id,parent_id,amount,note}
  - POST /api/admin/parents -> dodaj rodzica (invite opcjonalne)

## UI / Strony

- Public:
  - Strona główna: lista aktywnych zbiórek, skrócone sumy (zebrano/cel)
  - Strona zbiórki: opis i formularz "Sprawdź status" (email / numer ucznia)
- Admin:
  - Login
  - Dashboard: lista zbiórek, przycisk "Nowa zbiórka"
  - Widok zbiórki: lista rodziców i statusów; akcje: zaznacz zapłatę (po jednym lub masowo), export CSV

## Konteneryzacja (przykładowy fragment `docker-compose.yml`)

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: skarbek
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: skarbek
    volumes:
      - db-data:/var/lib/postgresql/data
  backend:
    build: ./backend
    env_file: ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      - db
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
volumes:
  db-data:
```

Uwagi: w środowisku produkcyjnym warto serwować zbudowany frontend przez nginx lub CDN.

## Bezpieczeństwo i prywatność

- Hasła admina: bcrypt/argon2.
- JWT z krótkim TTL.
- Walidacja wejścia, rate limiting na publiczne endpointy sprawdzające status.
- Opcjonalne: weryfikacja tożsamości rodzica (token e-mail / link) jeśli wymagane.

## Testy i jakość

- Backend: testy jednostkowe i integracyjne (pytest + TestClient FastAPI). Użyć testowej bazy Postgres (docker-compose.override) lub SQLite dla szybkich testów.
- Frontend: testy komponentów (Jest/React Testing Library) i e2e (Playwright/Cypress) jeśli potrzeba.

## Roadmap (kroki i estymaty)

1. Szkielet repo + docker-compose + minimalny endpoint GET /api/campaigns — 1 dzień
2. Modele DB + migracje + CRUD zbiórek — 2 dni
3. Frontend publiczny: lista + status check — 2 dni
4. Panel admina: login, tworzenie zbiórek, oznaczanie wpłat — 2 dni
5. Testy krytycznych przepływów + dokumentacja uruchomienia — 1 dzień
   Szacunkowo: 8 dni roboczych dla pojedynczego developera (zakres minimalny).

## Dalsze kroki (co mogę zrobić teraz)

- Jeśli potwierdzisz ten stack, przygotuję szkielet repo: katalogi `backend/`, `frontend/`, `infra/` i pliki startowe (Dockerfile, minimalny FastAPI app, minimalny React app) oraz `docker-compose.yml`.
- Możemy później dodać integrację z bramką płatności, powiadomienia e-mail oraz role w panelu admina.

## Pokrycie wymagań (status)

- Rodzice widzą zbiórki: Opis i endpoint zaprojektowany — Done (plan)
- Rodzice sprawdzają status płatności: Opis API/UX — Done (plan)
- Panel administracyjny: Opis funkcji i API — Done (plan)
- Hostowanie w Dockerze: Przygotowany fragment docker-compose — Done (plan)

---

Plik zapisany lokalnie w repo jako `plan.md`. Jeśli chcesz, od razu stworzę szkielety backend/frontend i uruchomię lokalnie build/testy.
