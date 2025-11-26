import base64
import logging
import os
from email.mime.text import MIMEText
from typing import Iterable, List, Optional

import google.auth.transport.requests
import requests
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

GMAIL_API_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
DEFAULT_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailEmailClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        sender_email: Optional[str] = None,
        parent_login_url: Optional[str] = None,
        token_uri: Optional[str] = None,
        scopes: Optional[Iterable[str]] = None,
    ):
        self.client_id = client_id or os.getenv("GMAIL_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GMAIL_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("GMAIL_REFRESH_TOKEN")
        self.sender_email = sender_email or os.getenv("GMAIL_SENDER_EMAIL")
        self.parent_login_url: str = self._build_parent_login_url(parent_login_url)
        self.token_uri = token_uri or os.getenv("GMAIL_TOKEN_URI", DEFAULT_TOKEN_URI)
        raw_scopes: List[str] = []
        if scopes:
            raw_scopes.extend(scopes)
        env_scopes = os.getenv("GMAIL_SCOPES")
        if env_scopes:
            raw_scopes.extend(env_scopes.split())
        self.scopes = raw_scopes or DEFAULT_SCOPES

    def _build_parent_login_url(self, override: Optional[str]) -> str:
        if override:
            return override
        env_login = os.getenv("PARENT_LOGIN_URL")
        if env_login:
            return env_login
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip('/')
        return f"{base_url}/#/parent/login"

    def _ensure_configured(self) -> None:
        if not all([self.client_id, self.client_secret, self.refresh_token, self.sender_email]):
            raise ValueError("Incomplete Gmail configuration: set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, GMAIL_SENDER_EMAIL")

    def _build_credentials(self) -> Credentials:
        self._ensure_configured()
        credentials = Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials

    def _create_message(self, to_email: str, subject: str, body: str) -> str:
        msg = MIMEText(body, "plain")
        msg["to"] = to_email
        sender = self.sender_email
        if sender is None:
            raise ValueError("Sender email is missing")
        msg["from"] = sender
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return raw

    def send_temporary_password_email(self, to_email: str, password: str, parent_name: Optional[str] = None) -> None:
        credentials = self._build_credentials()
        subject = "Twoje tymczasowe hasło do portalu Skarbek"
        body = (
            f"Cześć {parent_name or 'rodzicu'},\n\n"
            f"Wygenerowaliśmy dla Ciebie tymczasowe hasło: {password}\n"
            "Po pierwszym zalogowaniu musisz je zmienić.\n\n"
            f"Zaloguj się tutaj: {self.parent_login_url}\n\n"
            "Pozdrawiamy,\nZespół Skarbek"
        )
        raw = self._create_message(to_email, subject, body)
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }
        response = requests.post(GMAIL_API_URL, json={"raw": raw}, headers=headers)
        if not response.ok:
            logger.error("Gmail API returned %s: %s", response.status_code, response.text)
            response.raise_for_status()
        logger.info("Wysłano wiadomość e-mail do %s", to_email)


gmail_client = GmailEmailClient()
