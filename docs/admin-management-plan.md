# Plan implementacji: zarządzanie zbiórkami i rodzicami w panelu skarbnika

Data: 2025-10-12
Autor: (wygenerowane automatycznie)

## Cel
Dodać do panelu skarbnika (admin) możliwość zarządzania:
- Zbiórkami: zamknięcie, edycja, usuwanie.
- Rodzicami: ukrycie (soft-hide), zmiana hasła i adresu e-mail.

Rozwiązanie ma być bezpieczne (tylko role admin), odwracalne (soft-delete/soft-hide gdzie sensowne), i łatwe do przetestowania.

## Krótka umowa (contract)
- Wejścia: żądania HTTP z poprawnym admin JWT (nagłówek Authorization: Bearer ...).
- Wyjścia: JSON z kodami HTTP i treścią (sukces/blad + zaktualiziony obiekt). W przypadku edycji zwracamy zaktualizowany zasób.
- Tryby błędów: brak uprawnień (401/403), walidacja (400), zasób nie istnieje (404), konflikt danych (409).

## Edge case'y do obsłużenia
- Próba edycji/usunięcia już zamkniętej lub usuniętej zbiórki.
- Zmiana e-maila rodzica na taki, który już istnieje.
- Reset hasła rodzica — wysłanie e-maila nie jest obowiązkowe; można wymusić tymczasowe hasło lub wysłać token.
- Jeśli usunięcie zbiórki ma implikacje finansowe (wpłaty), wymusić potwierdzenie.
- Race conditions przy równoczesnych edycjach — walidacja wersji (optional: optimistic lock).

## Zmiany w modelu danych (baza)
- Campaign (zbiórka)
  - Dodaj pole: `is_closed: bool = False` (domyślnie False)
  - Opcjonalnie: `deleted_at: datetime | None` dla soft-delete

# Plan implementacji: zarządzanie zbiórkami i rodzicami w panelu skarbnika

Data: 2025-10-12

Autor: (wygenerowane automatycznie)

## Cel

Dodać do panelu skarbnika (admin) możliwość zarządzania:

- Zbiórkami: zamknięcie, edycja, usuwanie.

- Rodzicami: ukrycie (soft-hide), zmiana hasła i adresu e-mail.

Rozwiązanie ma być bezpieczne (tylko role admin), odwracalne (soft-delete/soft-hide gdzie sensowne), i łatwe do przetestowania.

## Krótka umowa (contract)

- Wejścia: żądania HTTP z poprawnym admin JWT (nagłówek Authorization: Bearer ...).

- Wyjścia: JSON z kodami HTTP i treścią (sukces/błąd + zaktualizowany obiekt). W przypadku edycji zwracamy zaktualizowany zasób.

- Tryby błędów: brak uprawnień (401/403), walidacja (400), zasób nie istnieje (404), konflikt danych (409).

## Edge case'y do obsłużenia

- Próba edycji/usunięcia już zamkniętej lub usuniętej zbiórki.

- Zmiana e-maila rodzica na taki, który już istnieje.

- Reset hasła rodzica — wysłanie e-maila nie jest obowiązkowe; można wymusić tymczasowe hasło lub wysłać token.

- Jeśli usunięcie zbiórki ma implikacje finansowe (wpłaty), wymusić potwierdzenie.

- Race conditions przy równoczesnych edycjach — walidacja wersji (optional: optimistic lock).

## Zmiany w modelu danych (baza)

- Campaign (zbiórka)

  - Dodaj pole: `is_closed: bool = False` (domyślnie False)

  - Opcjonalnie: `deleted_at: datetime | None` dla soft-delete

  - Opcjonalnie: `updated_by_admin_id` / `closed_by_admin_id`

- Parent (rodzic)

  - Dodaj pole: `is_hidden: bool = False` (ukrycie w UI, nadal w DB)

  - Hasła: już istniejące `password_hash` — dodaj endpoint do zmiany hasła (hashowanie po stronie serwera)

  - Email: aktualizowalne pole `email` (unikalność zachować lub wymusić)

> Uwaga: zamiast robić migracje (Alembic) w tej iteracji będziemy filtrować ukrytych rodziców po stronie backendu i NIE będziemy stosować migracji.
> Zamiast migracji opcjonalnie można usunąć starą bazę i odtworzyć schemat (patrz sekcja "DB reset" dalej).

## API — propozycja endpointów (backend)

Wszystkie endpointy wymagają roli: admin.

Campaigns:

- GET `/api/admin/campaigns` — lista zbiórek (z opcją ?include_closed=true)

- GET `/api/admin/campaigns/{campaign_id}` — szczegóły zbiórki

- POST `/api/admin/campaigns` — utwórz zbiórkę (istnieje już?)

- PUT `/api/admin/campaigns/{campaign_id}` — edytuj zbiórkę (body: editable fields)

- POST `/api/admin/campaigns/{campaign_id}/close` — zamknij zbiórkę (ustaw `is_closed=true`, zwróć historyczną info)

- DELETE `/api/admin/campaigns/{campaign_id}` — usuń zbiórkę

  - Implementacja zalecana: soft-delete (`deleted_at`) lub jeśli chcemy hard-delete — wymaga dodatkowej potwierdzenia i kontroli zależności (wpłaty).

Parents:

- GET `/api/admin/parents` — lista rodziców (domyślnie wyklucza rodziców oznaczonych jako ukryci; opcjonalnie `?include_hidden=true` aby je uwzględnić)

- GET `/api/admin/parents/{parent_id}` — szczegóły rodzica

- PUT `/api/admin/parents/{parent_id}` — edytuj dane (name, email)

- POST `/api/admin/parents/{parent_id}/change-password` — zmiana hasła (body: { new_password }) — serwer hashuje hasło

- POST `/api/admin/parents/{parent_id}/hide` — toggle ukrycia (`is_hidden = true`)

- POST `/api/admin/parents/{parent_id}/unhide` — przywrócenie widoczności

- DELETE `/api/admin/parents/{parent_id}` — opcjonalne usunięcie (zalecane soft-delete — ustaw pole `deleted_at` lub `is_hidden=true` + `deleted_by`)

W odpowiedziach będą zwracane zaktualizowane obiekty lub statusy.

## Backend — kroki implementacji (priorytetowo)

1. Schemat / DB reset (bez migracji)

    - Decyzja: NIE robimy migracji Alembic w tej iteracji. Zamiast tego mamy dwie opcje:

       1. Najbezpieczniejsza: dodać nowe pola w modelach i zmodyfikować kod tak, aby aplikacja tolerowała brak kolumn (używać domyślnych wartości) — ale to wymaga migracji, którą pomijamy.

       2. Szybsza (zgodnie z Twoim poleceniem): usunąć starą bazę danych i odtworzyć schemat z aktualnymi modelami. To powoduje utratę danych chyba, że wcześniej zrobimy backup/eksport.

    - Jeśli wybieramy opcję 2 (DB reset), kroki:

       - Zrobić pełny dump danych (pg_dump / sqlite copy) jako backup.

       - Zatrzymać aplikację, usunąć starą bazę (DROP) i utworzyć nową.

       - Uruchomić skrypt tworzący schemat (albo `sqlmodel`/ORM create_all) i ewentualne seedy (konto admina, demo dane).

       - Uruchomić aplikację i uruchomić testy integracyjne.

    - Uwaga: DB reset powoduje utratę historii (wpłat, logów) jeśli nie zachowamy/odtworzymy danych — rozważ wypakowanie krytycznych danych przed usunięciem.

2. Logika modelu

   - W modelu Campaign wymusić, że jeśli `is_closed == True`, nie pozwalamy na niektóre zmiany (np. zmiana kwoty docelowej) — zwracamy 409.

   - Dodaj helpery do soft-delete / hide.

3. API endpoints

   - Implementować endpointy opisane wyżej w `backend/app/api/admin.py` (dodaj nowe funkcje lub routery).

   - Walidacja wejścia (pydantic schemas): osobne schematy `CampaignUpdate`, `ParentUpdate`, `ChangePassword`.

   - Autoryzacja: użyć istniejącego admin dependency (np. `require_admin_user`) do zabezpieczenia.

4. Testy backend

   - Unit testy dla każdej operacji: zamknięcie, edycja (zarówno allowed i blocked), usuwanie, ukrywanie rodzica, zmiana e-mailu i hasła.

   - Integracyjne: zachowanie w DB, migracje.

5. API backwards compatibility

   - GET listy kampanii: domyślnie exclude closed/usunięte, jeśli klient poda flagę include_closed zwrócić wszystkie.

   - GET listy rodziców: domyślnie exclude ukryci rodzice; jeśli klient poda flagę `include_hidden=true` zwrócić również ukrytych.

   - Uwaga: ponieważ nie robimy migracji i (opcjonalnie) możemy zresetować bazę, kompatybilność historycznych danych może wymagać eksportu/importu. Jeśli wykonamy DB reset, konsumentów API (frontend) trzeba zsynchronizować z nowym schematem.

## Frontend — kroki implementacji (priorytetowo)

Ogólna zasada: nie pokazywać offline/hidden zasobów domyślnie; dodać UI potwierdzający usunięcie; logika odpowiedzialna za submit powinna obsłużyć błędy (walidacja, 409).

1. Nowe/przebudowane widoki / komponenty

   - `AdminCampaignsView` (lista zbiórek)

     - Tabela z każdą kampanią, kolumny: tytuł, data startu, data końca (jeśli jest), stan (otwarta/zamknięta), kwota oczekiwana, link do szczegółów, akcje: Edytuj, Zamknij, Usuń.

   - `CampaignEditView` (dedykowany widok/forma)

     - Formularz edycji wszystkich pól dozwolonych (walidacja), przycisk zapisz.

   - `ConfirmCloseModal` i `ConfirmDeleteModal` — modale z potwierdzeniem (jeśli kampania ma wpłaty, dodatkowe ostrzeżenie).

   - `AdminParentsView` (lista rodziców)

      - Tabela: imię/nazwisko, e-mail, status (ukryty/widoczny), ostatnie logowanie, akcje: Edytuj, Zmień hasło, Ukryj/Pokaż, Usuń.

      - UWAGA: rodzice oznaczeni jako `is_hidden=true` NIE POWINNI pojawiać się w tabeli domyślnie. Dodać opcjonalny przełącznik/filtr "Pokaż ukrytych" (oraz param `?include_hidden=true` po stronie API) jeśli admin chce je przeglądać lub przywrócić.

   - `ParentEditModal` — formularz zmiany e-maila i imienia.

   - `ParentChangePasswordModal` — formularz podawania nowego hasła (powtórz) i wysyłanie do endpointu.

2. API klienta (frontend)

   - Uzupełnić `frontend/src/api.js` o nowe funkcje:

     - adminListCampaigns(opts)

     - adminGetCampaign(id)

     - adminCreateCampaign(data)

     - adminUpdateCampaign(id, data)

     - adminCloseCampaign(id)

     - adminDeleteCampaign(id)

     - adminListParents(opts)

     - adminUpdateParent(id, data)

     - adminChangeParentPassword(id, newPassword)

     - adminHideParent(id) / adminUnhideParent(id)

   - Wszystkie wywołania muszą używać admin token z `auth.js` i obsługiwać 401/403.

3. UX/walidacja

   - Walidacja formularzy (np. e-mail format, hasło min. długość).

   - Feedback: toasty/sukces/error.

   - Podczas długich operacji (zamknięcie kampanii) pokazywać spinner/disabled button.

4. Testy frontend

   - Unit tests komponentów (jeśli są testy frontu).

   - Playwright / e2e: scenariusze: edycja kampanii, zamknięcie kampanii, usunięcie (potwierdzenie), edycja rodzica, zmiana hasła, ukryj/pokaż rodzica.

## Migracje i dane istniejące

- Przy dodawaniu `is_hidden` i `is_closed` warto ustawić domyślnie `False` i uruchomić migrację bez przerywania produkcji.

## Bezpieczeństwo i prywatność

- Tylko admin może wywoływać nowe endpointy — użyć istniejącej funkcji autoryzacji.

- Zmiana hasła: serwer hashuje hasło przy użyciu istniejącego mechanizmu (bcrypt/argon2), nie logujemy pełnych haseł.

- Dla zmiany e-maila rozważyć wymaganie ponownego potwierdzenia właściciela e-mail (opcja: wysłać potwierdzenie na nowe konto) — może być oznaczona jako "future enhancement".

## Testy

- Backend: testy jednostkowe i integracyjne (pytest)

- Frontend: Playwright smoke + e2e scenariusze (admin flow). Dodaj testy na: nieudolne wejścia, 401/403, 409 conflict.

## Rollout i migracja

1. Zaimplementować backend + migrację i przetestować lokalnie.

2. Wdróż na staging; uruchom migrację tam i uruchom testy integracyjne.

3. Wdróż na produkcję poza godzinami szczytu; monitoruj logs i błędy.

4. Jeśli masz soft-delete, przygotować narzędzie do odzyskiwania na wypadek potrzeby przywrócenia.

## Priorytety i estymacja (orientacyjnie)

- Schemat + migracja: 1–2 dni

- Backend endpoints + testy: 2–3 dni

- Frontend komponenty + toasty/walidacja: 2–3 dni

- E2E testy (Playwright) i end-to-end: 1–2 dni

- Całość: ~6–10 roboczych dni (zależnie od szczegółów i poziomu QA)

## Małe usprawnienia i opcje dodatkowe (propozycje)

- Dodanie `reason` lub `note` przy zamknięciu/usunięciu kampanii (log historyczny).

- Audyt zmian: tabela `admin_actions_log` z who/what/when dla krytycznych operacji.

- Wysyłka maili powiadomień do rodzica przy zmianie e-maila lub ukryciu konta (opcjonalnie).

- Implementacja optimistic concurrency (wersjonowania) dla kampanii, żeby uniknąć race conditions.

---

## Kolejne kroki które mogę wykonać teraz

- Przygotować migrację DB (plik Alembic) i PR z model changes.

- Zaimplementować backend endpoints (najpierw: Campaign close/edit/delete).

- Dodać API klienta i prosty UI w `AdminCampaignsView` i `AdminParentsView`.

Napisz proszę, od czego mam zacząć (backend czy frontend), albo czy mam najpierw wygenerować migrację i testy — wtedy od razu zacznę implementację.

---

## Nota o "dodawaniu brakujących kolumn przy starcie"

W tej iteracji zrezygnowaliśmy z pełnego systemu migracji (Alembic) na rzecz prostszej, bezpiecznej ścieżki deweloperskiej: przy uruchomieniu aplikacji `init_db()` wykonuje lekkie, idempotentne ALTER TABLE, które dodają brakujące kolumny (np. `parent.is_hidden`, `campaign.is_closed`, `campaign.deleted_at`) jeśli nie istnieją.

Dlaczego to robimy:
- Pozwala to szybko wdrożyć rozszerzenia modelu w środowisku deweloperskim i na stagingu bez konieczności od razu pisać i uruchamiać migracji.
- Unika natychmiastowych awarii aplikacji (500) gdy kod odwołuje się do nowych pól, a baza danych nadal ma stary schemat.

Ograniczenia i zalecenia:
- To nie zastępuje pełnych migracji dla produkcji. Dla środowisk produkcyjnych zalecane jest przygotowanie i przetestowanie skryptów migracyjnych (Alembic), planu backupu i, w razie potrzeby, okienka wydawniczego.
- ALTER TABLE wykonywane przy starcie jest „best-effort” i w niektórych środowiskach (ograniczone uprawnienia, specyficzne typy DB) może nie wykonać się. W takim wypadku uruchomienie powinno zgłosić i zablokować właściciela/operacje administracyjne.

W skrócie: to tymczasowy kompromis poprawiający developer experience; plan długoterminowy to migracje i formalne skrypty aktualizacji schematu.
