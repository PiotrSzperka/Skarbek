# Database Migrations

System zarządzania migracjami bazy danych dla projektu Skarbek.

## Struktura

```
backend/
├── migrations/           # Katalog z plikami migracji SQL
│   ├── 000_init_migration_system.sql
│   ├── 001_add_force_password_change.sql
│   └── ...
└── run_migrations.py    # Skrypt uruchamiający migracje
```

## Tabela audytowa

System automatycznie tworzy tabelę `schema_migrations` do śledzenia wykonanych migracji:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    checksum VARCHAR(64),
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE
);
```

## Użycie

### Uruchomienie migracji

```bash
# Z katalogu backend
python run_migrations.py
```

Lub poprzez Docker:

```bash
docker compose exec backend python run_migrations.py
```

### Automatyczne uruchamianie w CI/CD

Migracje są automatycznie uruchamiane podczas deploymentu poprzez GitHub Actions workflow `.github/workflows/cd.yml`:

```yaml
- name: Run database migrations
  run: |
    docker compose exec -T backend python run_migrations.py
```

Migracje wykonują się po zdeployowaniu kontenerów, zapewniając że schemat bazy danych jest zawsze aktualny.

### Zmienne środowiskowe

Skrypt używa `DATABASE_URL` z środowiska lub domyślnie:
```
postgresql://skarbek:skarbek@localhost:5432/skarbek
```

## Tworzenie nowej migracji

1. Utwórz plik w `migrations/` z numerem sekwencyjnym:
   ```
   002_nazwa_migracji.sql
   ```

2. Dodaj standardowy header z opisem:
   ```sql
   -- Migration: Krótki opis
   -- Date: YYYY-MM-DD
   -- Description: Szczegółowy opis zmian
   ```

3. Dodaj sprawdzenie czy migracja była już wykonana:
   ```sql
   DO $$
   BEGIN
       IF EXISTS (SELECT 1 FROM schema_migrations WHERE migration_name = '002_nazwa_migracji') THEN
           RAISE NOTICE 'Migration already executed, skipping';
           RETURN;
       END IF;
   END $$;
   ```

4. Napisz kod SQL migracji

5. Zapisz wykonanie w tabeli audytowej:
   ```sql
   INSERT INTO schema_migrations (migration_name, executed_at, success) 
   VALUES ('002_nazwa_migracji', NOW(), TRUE)
   ON CONFLICT (migration_name) DO NOTHING;
   ```

## Bezpieczeństwo

- ✅ Każda migracja może być uruchomiona wielokrotnie (idempotentność)
- ✅ Sprawdzanie przed wykonaniem czy migracja była już puszczona
- ✅ Rejestrowanie czasu wykonania i checksumu
- ✅ Zatrzymanie przy pierwszym błędzie
- ✅ Transakcyjność (rollback przy błędzie)

## Diagnostyka

### Sprawdzenie wykonanych migracji

```sql
SELECT * FROM schema_migrations ORDER BY executed_at DESC;

### Najlepsze praktyki

- Nigdy nie modyfikuj pliku migracji po jego zastosowaniu
- Każda migracja powinna być idempotentna (używaj `IF NOT EXISTS`, `IF EXISTS`)
- Testuj migracje na kopii bazy przed produkcją
- Dodawaj opisowe komentarze w plikach SQL
