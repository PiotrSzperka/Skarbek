# Dokumentacja: Funkcjonalność "Rodzice" (Admin dodaje rodziców)

## Cel

Dodanie możliwości, by każdy rodzic miał konto w systemie (tworzone przez admina), logował się i widział aktywne zbiórki oraz stan swoich wpłat.

## Zakres MVP

- Admin tworzy konto rodzica (email + hasło tymczasowe lub ustawione).
- Rodzic loguje się (email + password) i otrzymuje JWT.
- Rodzic widzi listę aktywnych kampanii i dla każdej informację o statusie płatności dla siebie (brak wpłaty / zgłoszona / opłacona) oraz historię własnych wpłat.
- Admin może przeglądać listę rodziców (opcjonalnie edytować/usunąć).

## API — kontrakt (MVP)

Prefiks: `/api/parents` (publiczne) oraz adminowe `/api/admin/parents` (admin tylko)

1. Admin: tworzenie rodzica

- POST `/api/admin/parents`
- Nagłówek: Authorization: Bearer <admin-token>
- Body JSON:
  {
  "name": "Jan Kowalski",
  "email": "jan@example.com",
  "password": "TymczasoweHaslo123" // opcja: wygenerowane przez system
  }
- Odpowiedź 201:
  {
  "id": 12,
  "name": "Jan Kowalski",
  "email": "jan@example.com"
  }
- Błędy: 400 (walidacja), 401 (brak/nieprawidłowy admin-token)

2. Rodzic: logowanie

- POST `/api/parents/login`
- Body JSON: { "email": "jan@example.com", "password": "TymczasoweHaslo123" }
- Odp 200: { "token": "<jwt>" }
- Token zawiera claim `sub` = email (lub parent_id) oraz `role`: "parent" i `exp`

3. Rodzic: profil

- GET `/api/parents/me` (Bearer token rodzica)
- Odp 200: { "id","name","email" }

4. Rodzic: lista aktywnych kampanii + status płatności

- GET `/api/parents/campaigns` (Bearer)
- Odp 200: [
  {
  "campaign": { "id","title","description","target_amount","due_date","active" },
  "contribution": { "id","amount_paid","status","paid_at","note" } | null
  },
  ...
  ]
- Zasada: jeśli brak contribution -> contribution=null; jeśli istnieje wiele zgłoszeń, można agregować (MVP: pokaż najnowszą lub sumę — ustalić)

5. Rodzic: historia wpłat

- GET `/api/parents/contributions`
- Odp: lista wpłat powiązanych z rodzicem

6. Rodzic: zgłoszenie wpłaty (opcjonalne MVP)

- POST `/api/parents/contributions`
- Body: { "campaign_id": 5, "amount": 50, "note": "przelew 01.10" }
- Odp 201: created contribution (status: "pending"), admin widzi i może oznaczyć jako paid

## Baza danych — zmiany modelu

W `backend/app/models.py`:

- Zaktualizować model `Parent`:
  - dodać `password_hash: Optional[str] = None`
  - dodać `created_at: datetime = Field(default_factory=datetime.utcnow)` (jeśli brak)

Relacje/konsekwencje:

- `Contribution.parent_id` powinien być FK do `Parent.id` (powinno już być)

SQL migracja (prosty ALTER, jeśli brak migracji):

```sql
ALTER TABLE parent ADD COLUMN password_hash text;
ALTER TABLE parent ADD COLUMN created_at timestamp WITH TIME ZONE DEFAULT now();
```

## Auth / bezpieczeństwo

- Hashowanie haseł: użyć istniejącego mechanizmu (passlib + pbkdf2_sha256), funkcje `hash_password`, `verify_password` (reuse z admina).
- JWT: użyć tego samego sekretu (`JWT_SECRET`), ale dodać claim `role: "parent"` lub `aud`/`sub` z prefixem.
- Token expiry: dodać `exp` (np. 7 dni dla rodzica).
- Admin tworzy rodziców — endpoint adminowy wymaga admin-token.

## Backend — implementacja (sugestia plików)

- `backend/app/api/parents.py` — nowy plik z endpointami:

  - `POST /admin/parents` (admin-only) — create parent
  - `POST /parents/login` — returns JWT
  - `GET /parents/me` — profile
  - `GET /parents/campaigns` — active campaigns + contribution status
  - `GET /parents/contributions` — history
  - `POST /parents/contributions` — submit payment (optional)

- Reuse:
  - `backend/app/auth.py` — dodać (lub reuse) `hash_password`, `verify_password`, `create_token` z `role` claim.
  - `backend/app/middleware.py` — możesz rozróżnić admin/parent roles albo w endpointach ręcznie dekodować token i sprawdzać role.

## Frontend — implementacja (sugestia)

- Komponenty (React):
  - `src/ParentLogin.jsx` — formularz logowania
  - `src/ParentDashboard.jsx` — lista aktywnych kampanii + statusy
  - (Opcjonalnie) `src/ParentRegister.jsx` — tylko jeśli chcesz publiczną rejestrację
- API helpery (`frontend/src/api.js`):
  - `parentLogin(email,password)`, `parentGetCampaigns(token)`, `parentGetContributions(token)`, `parentPostContribution`.
- Przechowywanie tokena: `localStorage` (MVP). Użyć `Authorization: Bearer <token>`.

## Przykłady curl (quick smoke tests)

1. Admin tworzy rodzica (admin-token z endpointu admin/login):

```bash
curl -X POST http://localhost:8000/api/admin/parents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{"name":"Jan Kowalski","email":"jan@example.com","password":"Temp1234"}'
```

2. Rodzic login:

```bash
curl -X POST http://localhost:8000/api/parents/login -H "Content-Type: application/json" -d '{"email":"jan@example.com","password":"Temp1234"}'
```

3. Rodzic pobiera kampanie:

```bash
curl -H "Authorization: Bearer <PARENT_TOKEN>" http://localhost:8000/api/parents/campaigns
```

## Edge-cases / decyzje do podjęcia

- Czy admin ustawia hasło, czy system wysyła link resetu? (MVP: admin ustawia tymczasowe hasło)
- Reguła agregacji wpłat (sumować vs najnowsza) — MVP: pokaż sumę `amount_paid` i status `paid` jeśli sum >= target.
- Czy rodzic może edytować profil/email? (opcjonalne)

## NOWE WYMAGANIE: Wymuszenie zmiany hasła przy pierwszym logowaniu rodzica

### Cel

Podnieść bezpieczeństwo kont rodziców poprzez wymuszenie ustawienia własnego, unikalnego hasła przy pierwszym logowaniu (po utworzeniu konta przez administratora lub resetowaniu hasła przez admina).

### Zakres

1. Każde nowo utworzone konto rodzica otrzymuje flagę `force_password_change = True`.
2. Rodzic loguje się hasłem tymczasowym nadanym przez admina (lub zresetowanym) – backend rozpoznaje flagę i zwraca informację, że wymagana jest zmiana hasła.
3. Do czasu zmiany hasła dostęp rodzica do zwykłych zasobów API (kampanie, zgłaszanie wpłat, lista wpłat) jest zablokowany — dozwolone są tylko dwa endpointy:

  - endpoint logowania
  - endpoint wymuszonej zmiany hasła (np. `POST /api/parents/change-password-initial`)

4. Po skutecznej zmianie hasła flaga `force_password_change` ustawiana jest na `False`, system zapisuje znacznik czasu `password_changed_at` (opcjonalnie), a rodzic otrzymuje „normalny” token.
5. Admin resetując hasło rodzica (funkcjonalność do dodania) również ponownie ustawia `force_password_change = True`.

### Zmiany w modelu danych

Model `Parent` (plik `backend/app/models.py`) – dodać pola:

```python
force_password_change: bool = Field(default=True)
password_changed_at: Optional[datetime] = None  # (opcjonalnie, do audytu)
```

Przykładowa migracja SQL (jeśli brak systemu migracji):

```sql
ALTER TABLE parent ADD COLUMN force_password_change boolean DEFAULT true;
ALTER TABLE parent ADD COLUMN password_changed_at timestamp with time zone NULL;
```

### Backend – zmiany API

1. `POST /api/admin/parents` – podczas tworzenia rodzica automatycznie ustawia `force_password_change = True`.
2. `POST /api/parents/login` – logika:

   - Weryfikuj hasło.
   - Jeśli `force_password_change == True` zwróć JSON z kluczem np.:

     ```json
     { "token": "<tymczasowy_jwt>", "require_password_change": true }
     ```

     Token może być (A) ograniczony tylko do endpointu zmiany hasła (np. claim `scope: password_change`) lub (B) pełny, ale autoryzacja innych endpointów go odrzuci przy aktywnej fladze.

3. NOWY endpoint: `POST /api/parents/change-password-initial`

   - Body: `{ "old_password": "Temp1234", "new_password": "NoweTrwaleHaslo!" }`
   - Wymagania:
     - Token ważny i (a) ma scope password_change lub (b) rodzic istnieje i ma `force_password_change = True`.
     - `new_password` != `old_password`.
     - (Opcjonalnie) wymusić minimalną długość / złożoność.
   - Efekt:
     - Aktualizacja `password_hash`.
     - `force_password_change = False`.
     - Ustawienie `password_changed_at = now()`.
     - Zwrócenie nowego pełnoprawnego JWT: `{ "token": "<new_jwt>", "force_password_change": false }`.

4. Middleware / guard w istniejących endpointach rodzica (`/parents/me`, `/parents/campaigns`, `/parents/contributions`, `/parents/contributions` POST):

   - Jeśli `force_password_change == True` → zwróć `403` z kodem `password_change_required` (lub `409` – wedle preferencji) i komunikatem.
   - Ten sam kod statusu pozwoli frontendowi na prosty redirect.

### Token i autoryzacja – rekomendacja

Najprostsze do wdrożenia: wydaj pełen JWT przy logowaniu (aby mieć identyczną obsługę nagłówka), ale w każdym chronionym endpointzie sprawdzaj flagę i blokuj dostęp dopóki nie zostanie zmienione hasło. Alternatywa (bardziej granularna) to osobny token „scoped” – większy nakład pracy, niekonieczne w MVP.

### Frontend – zmiany

1. Po udanym `login` jeśli `require_password_change === true` → zapisz tymczasowy token w `localStorage` i przejdź do nowej strony/komponentu: `ParentForcePasswordChange`.
2. Formularz zmiany hasła:
  - Pola: stare hasło, nowe hasło, powtórzenie nowego.
  - Walidacja klienta (min długość, różne od starego, dopasowanie powtórzenia).
3. Po sukcesie:
  - Nadpisz token w `localStorage` nowym.
  - Redirect do panelu rodzica (`/parent/dashboard`).
4. UI/UX: Wszystkie inne komponenty chronione powinny sprawdzać przy mount czy backend nie zwrócił `password_change_required` – jeśli tak, redirect.

### Testy (proponowane scenariusze)

Backend (pytest):

1. Utworzenie rodzica → `force_password_change` == True.
2. Login tymczasowym hasłem → 200 + `require_password_change: true`.
3. Próba pobrania kampanii przed zmianą hasła → 403 `password_change_required`.
4. Zmiana hasła endpointem → 200 + nowy token; flaga = False.
5. Ponowny login nowym hasłem → 200 bez `require_password_change`.
6. Reset hasła przez admina (gdy dodamy) ponownie ustawia flagę.

Frontend (e2e / integracja):

1. Login rodzica tymczasowym → redirect do formy zmiany hasła.
2. Błędne powtórzenie nowego hasła → walidacja klienta.
3. Sukces zmiany → dostęp do dashboardu.

### Edge Cases / ryzyka

| Przypadek | Obsługa |
|----------|---------|
| Rodzic próbuje użyć starego linku / tokenu po zmianie | Token działa do wygaśnięcia – akceptowalne w MVP; można rozważyć rotację secret / wersjonowanie tokenu przy zmianie hasła |
| Admin nadaje identyczne hasło jako poprzednie | Endpoint zmiany może blokować `new == old` |
| Brak `old_password` (rodzic zapomniał) | Osobny flow resetu hasła poza zakresem tego wymagania |
| Równoczesne logowanie z dwóch urządzeń przed zmianą | Oba zobaczą wymóg zmiany; pierwszy który zmieni odblokuje konto |

### Plan wdrożenia (kolejność)

1. Dodanie pól do modelu + migracja.
2. Modyfikacja endpointu tworzenia rodzica (ustaw flaga True).
3. Modyfikacja loginu – zwracanie `require_password_change`.
4. Dodanie endpointu `change-password-initial`.
5. Guard w istniejących endpointach rodzica.
6. Frontend: komponent wymuszonej zmiany hasła + redirecty.
7. Testy jednostkowe backend + szybkie e2e (login → wymuszenie → zmiana → dostęp).
8. Dokumentacja: (gotowe – niniejsza sekcja) + README / changelog.

### Dalsze ulepszenia (po MVP)

- Polityka złożoności haseł (min długość, znaki specjalne).
- Wymuszenie rotacji co X dni (wykorzystanie `password_changed_at`).
- Inwalidacja aktywnych tokenów po zmianie hasła (lista zbanowanych jti lub inkrementacja `token_version`).
- Email powiadamiający rodzica o zmianie hasła.

## Plan wdrożenia — następne kroki

- Potwierdź: admin tworzy rodziców (przyjęte).
- Zaimplementuję backendowe zmiany (models + `api/parents.py` + auth helpers).
- Dodam prosty admin UI (opcjonalnie) do tworzenia rodziców.
- Dodam frontend dla rodzica: login + dashboard.

Chcesz, żebym od razu zaimplementował backend (modele + endpointy) czy wolisz najpierw zmiany w DB/migrację lub UI admina? Jeśli backend — zaczynam od `backend/app/models.py` i `backend/app/api/parents.py`.
