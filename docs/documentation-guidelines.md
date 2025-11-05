# Dokumentacja projektu — wytyczne (PL)

Ten plik opisuje zasady tworzenia dokumentacji w repozytorium. Projekt przyjmuje dokumentowanie po polsku; proszę trzymać się poniższych reguł, aby dokumentacja była spójna i łatwa do przeglądania.

Podstawowe zasady
-----------------
- Język: polski. Wszystkie nowe pliki dokumentacji i zmiany w istniejących plikach opisowych powinny być po polsku.
- Lokalizacja plików: umieszczaj dokumenty w katalogu `docs/` w repo (np. `docs/plan-roster-po-polsku.md`).
- Pierwsza linia: używaj nagłówka poziomu 1 (H1) jako tytułu pliku Markdown, np. `# Tytuł dokumentu`.
- Styl nagłówków: stosuj atx (##, ###) zamiast setext (underline) — ułatwia to parsowanie i zapobiega lintowi.
- Formatowanie: trzymaj akapity krótkie, używaj list punktowanych dla zadań i numerowanych dla sekwencji kroków.
- Przykłady i JSON: wstawiaj bloki kodu z odpowiednim oznaczeniem języka (```json, ```bash, ```py).

Zawartość dokumentu
-------------------
Każdy ważny dokument powinien zawierać krótki nagłówek opisujący cel, następnie sekcję "Cel", "Zakres", "Wymagania/kontrakt API (jeśli dotyczy)", "Pliki do edycji" oraz "Kroki implementacji". Dodaj "Kryteria akceptacji" i "Przypadki brzegowe" gdy to ma sens.

Nazewnictwo plików
------------------
- Używaj czytelnych nazw po polsku, bez polskich znaków w nazwie pliku (np. `plan-roster-po-polsku.md`, `parenty-instrukcja.md`).
- Unikaj spacji; używaj myślników `-` jako separatorów.

Przykładowy minimalny szablon dokumentu
```md
# Tytuł dokumentu

Cel
----
Krótki opis celu dokumentu.

Zakres
-----
Co obejmuje dokumentacja.

Kontrakt API
-----------
Jeśli dotyczy: opis endpointów, kształt request/response.

Pliki do edycji
---------------
- `backend/app/api/...` — opis zmian
- `frontend/src/...` — opis zmian

Kroki implementacji
--------------------
1. Punkt pierwszy
2. Punkt drugi

Kryteria akceptacji
-------------------
- Lista rzeczy, które muszą działać, aby uznać zadanie za zakończone.
```

Wersjonowanie dokumentów
------------------------
- Jeśli dokument ulega znacznym zmianom, dodaj krótki wpis "Zmiany" z datą i opisem co się zmieniło.

Przykłady i dodatkowe wskazówki
-------------------------------
- Przy dłuższych procedurach dodaj sekcję "Jak testować lokalnie" z poleceniami do uruchomienia kontenerów, testów itp.
- Trzymaj instrukcje operacyjne (komendy docker, rebuild) w bloku ```bash```, tak aby dało się je łatwo skopiować.

Kontakt / właściciel dokumentacji
--------------------------------
- Jeśli dokument dotyczy konkretnej funkcjonalności, dopisz kto jest odpowiedzialny (imię/email) lub który issue/PR jest powiązany.

Jeśli chcesz, mogę teraz automatycznie przetłumaczyć istniejące ważne dokumenty (np. `docs/parents.md`, `README.md`) na polski i dodać je do `docs/` — napisz które pliki mam przerobić w pierwszej kolejności.
