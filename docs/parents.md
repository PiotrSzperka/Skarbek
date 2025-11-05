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

## Plan wdrożenia — następne kroki

- Potwierdź: admin tworzy rodziców (przyjęte).
- Zaimplementuję backendowe zmiany (models + `api/parents.py` + auth helpers).
- Dodam prosty admin UI (opcjonalnie) do tworzenia rodziców.
- Dodam frontend dla rodzica: login + dashboard.

Chcesz, żebym od razu zaimplementował backend (modele + endpointy) czy wolisz najpierw zmiany w DB/migrację lub UI admina? Jeśli backend — zaczynam od `backend/app/models.py` i `backend/app/api/parents.py`.
