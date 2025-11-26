# PostgreSQL admin UI

To explore or manage the backing Postgres database without touching CLI tools, the Proxmox stack now brings up a `pgadmin` container (image `dpage/pgadmin4`).

- The container exposes port `5050` on the host by passing `5050:5050` in `deploy/proxmox/docker-compose.yml`.
- You must set `PGADMIN_EMAIL` and `PGADMIN_PASSWORD` in `deploy/proxmox/.env`/`.env.local` (the workflow now copies them from the repository secrets) before starting the stack.
- Once the stack is up, visit `http://<host>:5050` (or `http://localhost:5050` during local development) and log in with those credentials.
- In pgAdmin, add a new server that connects to the `db` host using `${PGADMIN_EMAIL}`/`PGADMIN_PASSWORD` for authentication if needed.

For local testing you can copy `deploy/proxmox/.env.local.example`, fill the four Gmail secrets plus `PGADMIN_EMAIL`/`PGADMIN_PASSWORD`, and run `docker compose up` inside `deploy/proxmox` to have pgAdmin alongside the backend and frontend.
