# Copilot Instructions

- Enforce the forced password change flow for parents on their first login and propagate the `require_password_change` flag instead of relying on legacy messages.
- Keep the database migration system with the audit table (`schema_migrations`) and the `run_migrations.py` runner; all migrations must be idempotent and self-logging.
- Use the `password` field in payloads (the legacy `temporary_password` field is invalid) and expect English validation messages from the API.
- Treat protected parent endpoints as inaccessible until the password change is completed; tests should reflect this guard.
- In CI workflows, never push Docker images when the workflow is triggered by a pull request. Only login to Docker Hub and push images on direct pushes to the `main` branch.
