## Plan: Lista rodziców i wpłat dla każdej zbiórki

Cel
----
Umożliwić skarbnikowi (admin) przeglądanie dla każdej zbiórki listy rodziców z przypisaną do każdego z nich informacją o zgłoszonej wpłacie — statusie, kwotach oraz możliwością potwierdzenia wpłaty dla pojedynczego rodzica.

Główne założenia i kontrakt API
--------------------------------
- Nowy endpoint administracyjny: GET /api/admin/campaigns/{campaign_id}/roster
  - Cel: zwrócić listę rodziców i (jeśli istnieje) powiązany rekord wpłaty (contribution) dla danej zbiórki.
  - Kształt odpowiedzi (JSON):

```json
{
  "campaign": { "id": 123, "title": "X", "target_amount": 300.0 },
  "rows": [
    {
      "parent_id": 1,
      "parent_name": "Anna Kowalska",
      "parent_email": "anna@example.com",
      "contribution": {
        "id": 10,
        "amount_expected": 50.0,
        "amount_paid": 50.0,
        "status": "paid",
        "paid_at": "2025-11-03T10:00:00Z",
        "note": "potwierdzone"
      }
    },
    {
      "parent_id": 2,
      "parent_name": "Jan Nowak",
      "parent_email": "jan@example.com",
      "contribution": null
    }
  ]
}
```

Uwagi projektowe i założenia
----------------------------
- Lista powinna zawierać wszystkich (widocznych) rodziców i wykonywać LEFT JOIN do tabeli contributions po `parent_id` i `campaign_id`. Dzięki temu skarbnik zobaczy, kto nie zgłosił wpłaty.
- Tabela `contribution` zawiera już kolumny: campaign_id, parent_id, amount_expected, amount_paid, status, paid_at, note.
- Skarbnik powinien móc oznaczyć wpłatę jako opłaconą (endpoint istniejący: `POST /api/admin/contributions/mark-paid`) lub stworzyć nowy rekord wpłaty, jeśli go brak — proponuję dodać `POST /api/admin/contributions` do tworzenia zgłoszenia wpłaty przez admina.
- Zakładamy umiarkowaną liczbę rodziców na zbiórkę (kilkaset), więc pojedyncze zapytanie z LEFT JOIN jest akceptowalne.
- Zgodnie z wcześniejszą decyzją o braku migracji na tym etapie, kod będzie defensywnie tolerował brak kolumn w starych bazach (try/except używany w innych miejscach).

Koncept zapytania SQL
---------------------
SELECT p.id as parent_id, p.name, p.email,
       c.id as contribution_id, c.amount_expected, c.amount_paid, c.status, c.paid_at, c.note
FROM parent p
LEFT JOIN contribution c ON c.parent_id = p.id AND c.campaign_id = :campaign_id
WHERE p.is_hidden = false  -- opcjonalny filtr
ORDER BY p.name

Zadania implementacyjne (pliki do edycji)
-----------------------------------------
- Backend
  - `backend/app/api/admin.py` — dodać nowy endpoint `GET /admin/campaigns/{id}/roster` oraz (opcjonalnie) `POST /admin/contributions` do tworzenia rekordu wpłaty.
  - `backend/app/tests/test_admin_roster.py` — dodać test(y) integracyjne sprawdzające działanie endpointu.

- Frontend
  - `frontend/src/api.js` — dodać helpery `adminCampaignRoster(campaignId, token)` i `adminCreateContribution(payload, token)`.
  - `frontend/src/Admin.jsx` (lub nowy `AdminCampaignDetail.jsx`) — dodać widok/sekcję pokazującą listę rodziców dla zbiórki z możliwością potwierdzenia wpłaty.
  - `frontend/tests/...` — dodać e2e test sprawdzający widok roster i potwierdzanie wpłaty.

Przypadki brzegowe
-------------------
- Rodzic bez rekordu contribution -> zwrócić `contribution: null` (UI powinna umożliwić utworzenie zgłoszenia).
- Kilka rekordów contribution dla jednego parent+campaign — aktualnie założymy jeden rekord na parent+campaign; jeśli nie, wybierzemy pierwszy/ostatni (można później dodać unikalny constraint).
- Ukryci rodzice (`is_hidden`) — domyślnie wyłączamy z listy; admin może opcjonalnie załadować z `include_hidden=true`.

Bezpieczeństwo
--------------
- Endpoint adminowy — wymaga tokenu admina (Bearer). Frontend będzie używał tego samego schematu uwierzytelnienia co inne admin endpoints.

Kryteria akceptacji
-------------------
- GET `/api/admin/campaigns/{id}/roster` zwraca poprawne dane kampanii i listę rodziców z powiązanymi wpłatami (lub null dla brakujących).
- UI admina pokazuje wiersze per-parent, z przyciskiem potwierdzenia wpłaty, który ustawia `status='paid'` i uzupełnia `amount_paid` oraz `paid_at`.
- Testy backendowe dla endpointu przechodzą lokalnie.

Plan wdrożenia
--------------
1. Dodać endpoint GET roster i ewentualnie POST create-contribution; napisać test.
2. Dodać helpery w `frontend/src/api.js`.
3. Dodać komponent w panelu admina oraz akcje (potwierdź wpłatę).
4. Dodać e2e test i wykonać krótkie testy smoke lokalnie.
