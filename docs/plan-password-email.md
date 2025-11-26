# Plan: wysyłka losowego hasła startowego e-mailem

1. Wymagania i kontekst
   - Po utworzeniu rodzica przez skarbnika nie ma potrzeby podawania pola `password` w payloadzie `POST /api/admin/parents` ani formularzu frontendowym.
   - System generuje nowy, czytelny (łatwy do wpisania) losowy ciąg 10 znaków i używa go jako tymczasowego hasła.
   - Hasło trafia e-mailem do rodzica; wiadomość zawiera przypomnienie o konieczności zmiany hasła przy pierwszym logowaniu.
   - Wysyłka wiadomości wykorzystuje Gmail API z przechowywanymi sekretami.

2. Backend - logika tworzenia rodzica
   - W `backend/app/api/admin.py` przy `admin_create_parent`:
     - Usuń wymóg `password` z payloadu oraz elementu formularza frontendu.
     - Wygeneruj hasło tymczasowe za pomocą funkcji `generate_readable_password(length=10)` wykorzystującej zestaw znaków bez łatwo mylonych symboli.
     - Zapisz hash hasła i pozostaw `force_password_change=True`, `password_changed_at=None`.
     - Dodaj testy walidujące długość i zestaw znaków wygenerowanego hasła.
   - Dodaj serwis e-mail (np. `backend/app/email.py`) obsługujący:
     - ładowanie `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_SENDER_EMAIL`, opcjonalnie `GMAIL_TOKEN_URI` i `GMAIL_SCOPES`,
     - uzyskiwanie lub odświeżanie tokenu dostępowego (np. `google.oauth2.credentials.Credentials` + `google.auth.transport.requests.Request` lub ręczny HTTP POST),
     - tworzenie MIME i wysyłkę przez Gmail API (`/gmail/v1/users/me/messages/send`),
     - logowanie błędów i zwracanie czytelnego wyjątku w razie awarii.
   - Po zapisaniu rodzica wywołaj serwis e-mail z adresem i hasłem.
   - Umożliw testowanie przez wstrzykiwalny klient e-mailowy (fixture w pytest).

3. Frontend - usuń pole hasła
   - W `frontend/src/AdminCreateParent.jsx` i pokrewnych komponentach usuń pola `password` oraz związany label/button.
   - Po udanym utworzeniu wyświetl komunikat, że hasło zostało wysłane e-mailem.
   - W `frontend/src/api.js` `adminCreateParent` nie wysyła danych o haśle.

4. Testy backendowe
   - Zaktualizuj `test_force_password_change.py` i/lub stwórz nowy test w `backend/tests/test_admin_management.py`:
     - Tworzenie rodzica nie wymaga pola `password`.
     - Hasło w bazie ma 10 znaków z zestawu dozwolonych.
     - Po utworzeniu wywoływany jest mockowany klient Gmail z odpowiednim adresem i treścią.
   - Dodaj fixture `fake_email_client` (np. w `tests/conftest.py`) i wstrzykuj go podczas testowania endpointu `admin_create_parent`.
   - Opcjonalnie dodaj test, który symuluje błąd Gmail API i oczekuje 500/odpowiedniego logu.

5. Testy frontendowe
   - Zaktualizuj Playwright (jeśli testują tworzenie rodzica) by nie oczekiwały pola hasła i by zweryfikowały pojawienie się komunikatu o wysyłce maila.

6. Konfiguracja Gmail API i sekrety
   - W dokumentacji (`docs/SETUP-LOCAL.md`, `.env.example`, `deploy/proxmox/.env.example`) dodaj:
     - `GMAIL_CLIENT_ID` oraz `GMAIL_CLIENT_SECRET` (OAuth 2.0 z konsoli Google).
     - `GMAIL_REFRESH_TOKEN` (uzyskany po jednorazowej autoryzacji, przechowywany jako secret).
     - `GMAIL_SENDER_EMAIL` (kontrola nad polem `From`).
     - Opcjonalnie `GMAIL_TOKEN_URI`/`GMAIL_SCOPES` dla niestandardów lub testów.
   - Wskazówki wdrożeniowe: te sekrety muszą być ustawione w środowiskach (docker-compose/env files oraz CI/CD secrets) i przekazywane do kontenera backendu.
   - W dokumentacji podaj krótki opis, jak odświeżyć `GMAIL_REFRESH_TOKEN` (np. prosty skrypt python używający `google-auth-oauthlib`).

7. Dokumentacja dla zespołu
   - Zaktualizuj `docs/SETUP-LOCAL.md` lub dodaj oddzielny rozdział o konfiguracji Gmail API i nowej funkcji.
   - Notuj wymagane zmienne środowiskowe oraz sposób testowania (mock Gmaila w pytest/CI).

8. Kolejne kroki
   - Po akceptacji planu implementacja backendu (generator, Gmail API, testy), frontend, dokumentacja.
   - Dodaj testy integracyjne/mocks i ew. e2e.

Po potwierdzeniu kierunku możemy rozpocząć implementację i dodać testy.
