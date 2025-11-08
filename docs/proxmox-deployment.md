# Deploying Skarbek on Proxmox Ubuntu VM (Docker)

This guide walks through running the Skarbek stack (PostgreSQL, FastAPI backend, and React/Vite frontend) on an Ubuntu 24.04 virtual machine hosted in Proxmox. The deployment uses the Docker images produced by CI and orchestrates them with Docker Compose.

## 1. Prerequisites

1. **Ubuntu 24.04 VM** on your Proxmox host with outbound internet access.
2. **Docker Engine + Compose plugin** installed on the VM. On a fresh Ubuntu install you can run:

   ```bash
   sudo apt update
   sudo apt install -y ca-certificates curl gnupg
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt update
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. (Optional) **Docker Hub login** if the repository is private.

## 2. Fetch deployment assets

Clone the repository (or copy the `deploy/proxmox` directory if you only want the deployment files):

```bash
git clone https://github.com/PiotrSzperka/Skarbek.git
cd Skarbek/deploy/proxmox
```

## 3. Configure environment variables

1. Copy the example environment file and edit the values:

   ```bash
   cp .env.example .env
   nano .env
   ```

2. Change the placeholder passwords/secrets:
   - `POSTGRES_PASSWORD`: database password used by Postgres and the backend
   - `ADMIN_PASSWORD`: initial admin login for the app
   - `JWT_SECRET`: random string for signing tokens
   - Update `BACKEND_IMAGE` / `FRONTEND_IMAGE` if you want a specific tag (e.g. `:main-<short-sha>`).

## 4. Start the stack

From the `deploy/proxmox` directory run:

```bash
docker compose pull
docker compose up -d
```

This starts three services:

- `db` (PostgreSQL 15) with persistent volume `db-data`
- `backend` (FastAPI) exposed on port `8000`
- `frontend` (Nginx serving the static build) exposed on port `3000`


Verify containers are healthy:

```bash
docker compose ps
```

## 5. Access the application

- Frontend UI: `http://<VM-IP>:3000`
- Backend API (optional direct access): `http://<VM-IP>:8000/docs`
- Default admin credentials: `admin` / the password you set in `.env`

## 6. Managing the stack

- View logs: `docker compose logs -f backend` or `frontend`
- Restart services: `docker compose restart frontend`
- Stop everything: `docker compose down`
- Remove volumes (drops the database): `docker compose down -v`

## 7. Updating to a new release

1. Pull the latest images:

   ```bash
   docker compose pull
   ```

2. Recreate containers with the new images:

   ```bash
   docker compose up -d
   ```

## 8. Optional hardening

- Replace default credentials with secure values.
- Consider moving secrets to Docker secrets or an external manager if you run in production.
- Restrict external access (e.g., Traefik/NGINX reverse proxy with HTTPS) or tunnel connections through your Proxmox host.
- Configure automated backups for the Postgres volume (`db-data`).

## 9. Automated deployments from GitHub Actions

The repository ships with a workflow (`.github/workflows/cd.yml`) that deploys straight from a **self-hosted runner** on the Proxmox VM. Because the runner already lives on the target machine, the workflow simply runs `docker compose` locally—no SSH or file copying required. It is still **manual-only** (`workflow_dispatch`) so you stay in control of when updates roll out.

### Required repository secrets

Set deployment secrets under **Settings → Secrets and variables → Actions** using one of the following approaches:

#### Option A – single-file secret (simple, current default)

| Secret | Description |
| --- | --- |
| `PROXMOX_ENV_FILE` | Literal contents of the `.env` file (can be multi-line) |

> Generate the `.env` locally, then copy its contents into the secret. Whenever you need to rotate secrets, update the GitHub secret—the workflow will rewrite `deploy/proxmox/.env` on the runner before redeploying.

#### Option B – individual secrets (fine-grained control)

If `PROXMOX_ENV_FILE` is **not** set, the workflow expects these secrets instead and will generate the `.env` file on the fly:

| Secret | Notes |
| --- | --- |
| `DEPLOY_POSTGRES_PASSWORD` | Required; used by Postgres and the backend |
| `DEPLOY_ADMIN_PASSWORD` | Required; initial admin password |
| `DEPLOY_JWT_SECRET` | Required; JWT signing key |
| `DEPLOY_BACKEND_IMAGE` | Optional override; defaults to `peterszp/skarbek-backend:latest` |
| `DEPLOY_FRONTEND_IMAGE` | Optional override; defaults to `peterszp/skarbek-frontend:latest` |
| `DEPLOY_BACKEND_HOST_PORT` | Optional; defaults to `8000` (host side of backend) |
| `DEPLOY_FRONTEND_HOST_PORT` | Optional; defaults to `3000` (host side of frontend) |
| `DEPLOY_POSTGRES_USER` | Optional; defaults to `skarbek` |
| `DEPLOY_POSTGRES_DB` | Optional; defaults to `skarbek` |
| `DEPLOY_ADMIN_USER` | Optional; defaults to `admin` |

> Keep the optional secrets unset to use the defaults that ship with the repository.

### Running the workflow

1. Make sure the self-hosted runner is online (see section 10 below).
2. In GitHub, open **Actions → Deploy to Proxmox → Run workflow**.
3. (Optional) clear the "Pull images" checkbox if you only want to restart the stack with images already present on the VM.
4. Watch the job logs. The runner performs:
   - `docker compose pull` (when requested)
   - `docker compose up -d` to deploy/restart containers
   - `python run_migrations.py` inside the backend container to apply pending database migrations

After the run finishes, check the VM (`docker compose ps`) to confirm the new containers are up. Database schema will be automatically updated to the latest version.

---
This setup gives you an always-on deployment that mirrors what CI builds and pushes to Docker Hub. Let me know if you want to add HTTPS, monitoring, or automation (e.g., Ansible) on top of this base configuration.

## 10. Installing a self-hosted GitHub Actions runner on the VM

When the Proxmox VM sits behind NAT, the GitHub-hosted runners cannot reach it over SSH. Instead, install a **self-hosted runner** directly on the VM and let the deployment workflow target that runner label.

1. Create a dedicated user that will own the runner and can talk to Docker:

   ```bash
   sudo useradd -m -s /bin/bash gha-runner
   sudo usermod -aG docker gha-runner
   ```

2. Switch to that user and download the latest Linux x64 runner release (replace the URL if GitHub publishes a newer version):

   ```bash
   sudo -iu gha-runner
   mkdir -p ~/actions-runner && cd ~/actions-runner
   curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.317.0/actions-runner-linux-x64-2.317.0.tar.gz
   tar xzf actions-runner.tar.gz
   ```

3. Register the runner with your repository. Use the registration token from **Settings → Actions → Runners → New self-hosted runner** and add a custom label (e.g., `proxmox`):

   ```bash
   ./config.sh --url https://github.com/PiotrSzperka/Skarbek --token <REGISTRATION_TOKEN> --labels proxmox
   ```

   > Running `config.sh` as `gha-runner` avoids the "Must not run with sudo" error. The script writes configuration under the user's home directory.

4. Exit the `gha-runner` shell once the configuration succeeds:

   ```bash
   exit
   ```

5. Install and start the runner as a systemd service so it survives reboots (still from `/home/gha-runner/actions-runner`):

   ```bash
   cd /home/gha-runner/actions-runner
   sudo ./svc.sh install gha-runner
   sudo ./svc.sh start
   ```

6. Back in GitHub, update `.github/workflows/cd.yml` to run on the `self-hosted` + `proxmox` label so deploys execute on this VM instead of a GitHub-hosted runner.

> **Quick test:** you can start the runner interactively as `gha-runner` via `./run.sh`. When you are satisfied, rely on the systemd service for day-to-day operations.

> **Fallback:** If you *must* run the runner as root (not recommended), export `RUNNER_ALLOW_RUNASROOT=1` before running `./config.sh` and `./run.sh`. Treat this only as a temporary workaround.
