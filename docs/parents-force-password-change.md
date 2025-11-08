# Wymuszenie zmiany hasła przy pierwszym logowaniu rodzica

## Cel

Podnieść bezpieczeństwo kont rodziców poprzez wymuszenie ustawienia własnego, unikalnego hasła przy pierwszym logowaniu (po utworzeniu konta przez administratora lub resetowaniu hasła przez admina).

## Zakres

1. Każde nowo utworzone konto rodzica otrzymuje flagę `force_password_change = True`.
2. Rodzic loguje się hasłem tymczasowym nadanym przez admina (lub zresetowanym) – backend rozpoznaje flagę i zwraca informację, że wymagana jest zmiana hasła.
3. Do czasu zmiany hasła dostęp rodzica do zwykłych zasobów API (kampanie, zgłaszanie wpłat, lista wpłat) jest zablokowany — dozwolone są tylko dwa endpointy:

   - endpoint logowania
   - endpoint wymuszonej zmiany hasła (np. `POST /api/parents/change-password-initial`)

4. Po skutecznej zmianie hasła flaga `force_password_change` ustawiana jest na `False`, system zapisuje znacznik czasu `password_changed_at` (opcjonalnie), a rodzic otrzymuje „normalny" token.
5. Admin resetując hasło rodzica (funkcjonalność do dodania) również ponownie ustawia `force_password_change = True`.

## Zmiany w modelu danych

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

## Backend – zmiany API

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

## Token i autoryzacja – rekomendacja

Najprostsze do wdrożenia: wydaj pełen JWT przy logowaniu (aby mieć identyczną obsługę nagłówka), ale w każdym chronionym endpointcie sprawdzaj flagę i blokuj dostęp dopóki nie zostanie zmienione hasło. Alternatywa (bardziej granularna) to osobny token „scoped" – większy nakład pracy, niekonieczne w MVP.

## Frontend – zmiany

1. Po udanym `login` jeśli `require_password_change === true` → zapisz tymczasowy token w `localStorage` i przejdź do nowej strony/komponentu: `ParentForcePasswordChange`.
2. Formularz zmiany hasła:
   - Pola: stare hasło, nowe hasło, powtórzenie nowego.
   - Walidacja klienta (min długość, różne od starego, dopasowanie powtórzenia).
3. Po sukcesie:
   - Nadpisz token w `localStorage` nowym.
   - Redirect do panelu rodzica (`/parent/dashboard`).
4. UI/UX: Wszystkie inne komponenty chronione powinny sprawdzać przy mount czy backend nie zwrócił `password_change_required` – jeśli tak, redirect.

## Testy (proponowane scenariusze)

### Backend (pytest)

1. Utworzenie rodzica → `force_password_change` == True.
2. Login tymczasowym hasłem → 200 + `require_password_change: true`.
3. Próba pobrania kampanii przed zmianą hasła → 403 `password_change_required`.
4. Zmiana hasła endpointem → 200 + nowy token; flaga = False.
5. Ponowny login nowym hasłem → 200 bez `require_password_change`.
6. Reset hasła przez admina (gdy dodamy) ponownie ustawia flagę.

### Frontend (e2e / integracja)

1. Login rodzica tymczasowym → redirect do formy zmiany hasła.
2. Błędne powtórzenie nowego hasła → walidacja klienta.
3. Sukces zmiany → dostęp do dashboardu.
4. **Pełny test e2e end-to-end**:
   - Admin tworzy nowego rodzica z hasłem tymczasowym.
   - Rodzic loguje się tymczasowym hasłem.
   - System przekierowuje do formularza zmiany hasła.
   - Rodzic wypełnia formularz (stare hasło, nowe hasło, powtórzenie) i zatwierdza.
   - System zapisuje nowe hasło i przekierowuje do dashboardu.
   - Rodzic wylogowuje się.
   - Rodzic loguje się ponownie nowym hasłem.
   - System pozwala na dostęp do dashboardu bez wymogu zmiany hasła.

## Edge Cases / ryzyka

| Przypadek | Obsługa |
|----------|---------|
| Rodzic próbuje użyć starego linku / tokenu po zmianie | Token działa do wygaśnięcia – akceptowalne w MVP; można rozważyć rotację secret / wersjonowanie tokenu przy zmianie hasła |
| Admin nadaje identyczne hasło jako poprzednie | Endpoint zmiany może blokować `new == old` |
| Brak `old_password` (rodzic zapomniał) | Osobny flow resetu hasła poza zakresem tego wymagania |
| Równoczesne logowanie z dwóch urządzeń przed zmianą | Oba zobaczą wymóg zmiany; pierwszy który zmieni odblokuje konto |

## Plan wdrożenia (kolejność)

1. Dodanie pól do modelu + migracja.
2. Modyfikacja endpointu tworzenia rodzica (ustaw flaga True).
3. Modyfikacja loginu – zwracanie `require_password_change`.
4. Dodanie endpointu `change-password-initial`.
5. Guard w istniejących endpointach rodzica.
6. Frontend: komponent wymuszonej zmiany hasła + redirecty.
7. Testy jednostkowe backend.
8. **Test e2e end-to-end** (Playwright/Cypress):
   - Admin tworzy nowego rodzica z hasłem tymczasowym.
   - Rodzic loguje się tymczasowym hasłem.
   - System przekierowuje do formularza zmiany hasła.
   - Rodzic wypełnia formularz (stare hasło, nowe hasło, powtórzenie) i zatwierdza.
   - System zapisuje nowe hasło i przekierowuje do dashboardu.
   - Rodzic wylogowuje się.
   - Rodzic loguje się ponownie nowym hasłem.
   - System pozwala na dostęp do dashboardu bez wymogu zmiany hasła.
9. Dokumentacja: README / changelog.

## Dalsze ulepszenia (po MVP)

- Polityka złożoności haseł (min długość, znaki specjalne).
- Wymuszenie rotacji co X dni (wykorzystanie `password_changed_at`).
- Inwalidacja aktywnych tokenów po zmianie hasła (lista zbanowanych jti lub inkrementacja `token_version`).
- Email powiadamiający rodzica o zmianie hasła.
