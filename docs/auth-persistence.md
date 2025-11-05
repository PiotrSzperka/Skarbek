# Utrzymanie sesji (persisted login) i przycisk wylogowania

## Cel
Umożliwić użytkownikom pozostawanie zalogowanym po przeładowaniu strony lub przejściu między podstronami oraz dodać przycisk „Wyloguj”, który kończy sesję i czyści zapisane dane autoryzacyjne.

Zakres: proste rozwiązanie oparte na JWT przechowywanym w localStorage. Nie obejmuje refresh-tokenów ani cookie httpOnly (można rozwinąć później).

## Krótka umowa
- Token JWT będzie zapisywany w localStorage (klucze `parent_token` i `admin_token`).
- Przy starcie aplikacji (root/App) odczytamy token z localStorage i ustawimy stan aplikacji.
- `api.request` będzie automatycznie dołączał Authorization: Bearer <token> jeśli token istnieje.
- Logout usuwa token(y) z localStorage oraz czyści stan React i przekierowuje na stronę logowania.
- Przy 401 automatycznie wywołamy logout (poprawa UX przy wygasłym tokenie).

## Plan działania (kroki)
1. Centralny helper auth
   - Dodaj `frontend/src/auth.js` z funkcjami:
     - `setAdminToken(token)`, `setParentToken(token)`, `getToken()`, `clearTokens()`, `isLoggedIn()`.
     - Możliwość podpięcia callbacku onLogout (opcjonalne).

2. Zapis tokenu przy logowaniu
   - `ParentLogin.jsx`: zapisz token w `localStorage.setItem('parent_token', token)` (już jest, upewnić się).
   - `Admin.jsx`: po adminLogin zapisz `localStorage.setItem('admin_token', token)` oraz ustaw stan.

3. Inicjalizacja stanu po załadowaniu aplikacji
   - `frontend/src/main.jsx` lub `App.jsx`: w `useEffect` odczytaj tokeny z localStorage i ustaw globalny stan (np. context lub props):
     - `const token = localStorage.getItem('parent_token') || localStorage.getItem('admin_token')`
     - jeśli token istnieje, ustaw go w stanie i opcjonalnie wywołaj `/api/parents/me` by zweryfikować ważność.

4. Automatyczne dołączanie Authorization w `api.js`
   - W `request()` przed fetchem pobierz token z localStorage (o ile nie przekazano Authorization w opts.headers) i dołącz nagłówek:

```javascript
function getStoredToken() {
  return localStorage.getItem('admin_token') || localStorage.getItem('parent_token') || null;
}

async function request(path, opts = {}) {
  const mergedHeaders = {...(opts.headers || {})};
  const tokenFromStorage = getStoredToken();
  const headers = { 'Content-Type': 'application/json', ...(tokenFromStorage && !mergedHeaders.Authorization ? { Authorization: `Bearer ${tokenFromStorage}` } : {}), ...mergedHeaders };
  const res = await fetch(`${apiBase}${path}`, { ...opts, headers });
  if (res.status === 401) {
    // opcjonalnie: clear tokens + emit logout
    localStorage.removeItem('parent_token');
    localStorage.removeItem('admin_token');
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json().catch(() => null)
}
```

5. Logout UI i handler
   - Dodaj przycisk `Wyloguj` w komponentach `Admin` i `ParentDashboard` (np. w nagłówku).
   - Handler `logout()`:
```javascript
function logout() {
  localStorage.removeItem('parent_token');
  localStorage.removeItem('admin_token');
  // zresetuj stan React (np. setToken(null), setUser(null))
  window.location = '/'; // lub router.push('/login')
}
```

6. Obsługa 401 (w `api.request` lub globalnie)
   - Jeśli backend zwróci 401, wykonaj `logout()` automatycznie i pokaż komunikat "Sesja wygasła".
   - Dodatkowo nasłuchuj eventu `storage` by obsłużyć logout w wielu kartach:
```javascript
window.addEventListener('storage', (e) => {
  if (e.key === 'parent_token' && e.newValue === null) { /* handle logout in this tab */ }
});
```

## Pliki do zmiany
- `frontend/src/api.js` — automatyczne dołączanie tokenu i obsługa 401 (fragment powyżej).
- `frontend/src/ParentLogin.jsx` — upewnić się, że zapisuje `parent_token` (już jest).
- `frontend/src/Admin.jsx` — zapisz `admin_token` po zalogowaniu.
- `frontend/src/App.jsx` / `main.jsx` — inicjalizacja stanu z localStorage.
- `frontend/src/Header.jsx` (nowy/opcjonalny) — przycisk `Wyloguj`.
- `frontend/src/auth.js` (opcjonalnie) — helper do zarządzania tokenami.

## Przykładowe UX flow
- Logowanie rodzica: po otrzymaniu tokenu -> `localStorage.setItem('parent_token', token)` -> setState(token) -> przekieruj do dashboard.
- Odświeżenie strony: App useEffect odczytuje token, ustawia stan -> dashboard od razu widoczny.
- Klik Wyloguj: usuń tokeny, czyść stan, przekieruj do logowania.

## Edge cases i bezpieczeństwo
- LocalStorage = prosty, ale podatny na XSS. Dla większego bezpieczeństwa preferowane httpOnly cookies + refresh tokeny.
- Warto rozważyć mechanizm automatycznego odświeżania tokena (refresh token) jeśli chcemy dłuższych sesji bez przelogowania.
- Multi-tab: użyj eventu `storage` do propagacji logout.

## Testy
- Manualne: logowanie → F5 → nadal zalogowany; klik logout → przekierowanie; po logout F5 → brak autoryzowanego dostępu.
- Automatyczne: Playwright/Cypress e2e test logowania, odświeżania i logout.
- Jednostkowe: funkcje helperów auth.

## Estymacja czasu
- Prosty PR (localStorage + logout + automatyczne dodawanie header + handling 401): ~30–60 minut (frontend only).
- Dodanie React Context/centralnego store i testów e2e: +1–2 godziny.
- Pełne bezpieczne rozwiązanie (httpOnly cookies + refresh tokens + backend changes): kilka godzin do dnia pracy.

## Kolejne kroki (opcjonalnie, co mogę zrobić dalej)
- Wdrażam teraz prostą wersję (localStorage + logout) i przebudowuję frontend; uruchomię szybkie testy.
- Albo najpierw przygotowuję PR z patchami i opisem, byś mógł je przejrzeć.

---

Jeśli chcesz, mogę od razu zaimplementować prostą wersję i uruchomić rebuild frontend (ok. 30–60 minut). Napisz, czy mam przejść do implementacji teraz.