import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def load_env(path: Path) -> dict:
    result = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def main():
    env = load_env(Path(__file__).resolve().parent.parent / "deploy" / "proxmox" / ".env.local")
    client_id = env.get("GMAIL_CLIENT_ID")
    client_secret = env.get("GMAIL_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in deploy/proxmox/.env.local")

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8080/")

    try:
        creds = flow.run_local_server(open_browser=False, prompt="consent")
    except Exception as exc:
        print("Unable to open a browser or bind to localhost:8080. Falling back to manual flow.")
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            access_type="offline",
        )
        print(auth_url)
        auth_response = input("Paste the full redirect URL after you approve consent: ")
        flow.fetch_token(authorization_response=auth_response)
        creds = flow.credentials
    if not creds.refresh_token:
        raise SystemExit("did not receive a refresh token — make sure "
                         "the OAuth client is Desktop type and you select "
                         "the correct account during auth")
    print("Copy the following into deploy/proxmox/.env.local:")
    print("GMAIL_REFRESH_TOKEN=" + creds.refresh_token)


if __name__ == "__main__":
    main()
