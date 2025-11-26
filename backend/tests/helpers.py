from fastapi.testclient import TestClient


def create_parent_and_capture_password(client: TestClient, token: str, fake_email_client, email: str, name: str) -> tuple:
    headers = {'Authorization': f'Bearer {token}'}
    response = client.post('/api/admin/parents', json={'name': name, 'email': email}, headers=headers)
    assert response.status_code == 200
    sent = fake_email_client.sent[-1]
    assert sent['to_email'] == email
    assert sent['parent_name'] == name
    return response, sent['password']
