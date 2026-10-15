
import io
import uuid
import fitz
from sqlalchemy import text
from server import app
from pathlib import Path

def make_user(client):
    unique = uuid.uuid4().hex
    details = {
        "email": f"a02-{unique}@example.com",
        "login": f"a02-{unique}",
        "password": "a02-test-password",
    }
    response = client.post('/api/create-user', json=details)
    assert response.status_code == 201, f'create-user: {response.status_code} {response.get_json()}'
    user_id = response.get_json()['id']
    response = client.post('/api/login', json={'email': details['email'], 'password': details['password']})
    assert response.status_code == 200, f'login: {response.status_code} {response.get_json()}'
    return user_id, {'Authorization': f'Bearer {response.get_json()["token"]}'}

def make_pdf():
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), 'A-02 ownership baseline')
        return pdf.tobytes()

def safe_test_file(path, storage_root):
    resolved = Path(path).resolve()
    if resolved.is_relative_to(storage_root.resolve()):
        resolved.unlink(missing_ok=True)

def main():
    client = app.test_client()
    created_users = []
    doc_id = None
    try:
        owner_id, owner_headers = make_user(client)
        created_users.append(owner_id)
        other_id, other_headers = make_user(client)
        created_users.append(other_id)

        upload = client.post('/api/upload-document', headers=owner_headers,
                             data={'file': (io.BytesIO(make_pdf()), 'a02-baseline.pdf')})
        assert upload.status_code == 201, f'upload: {upload.status_code} {upload.get_json()}'
        doc_id = upload.get_json()['id']
        print(f'Test document ID: {doc_id}; owner user ID: {owner_id}; other user ID: {other_id}')

        body = {
            'method': 'visible-hmac',
            'intended_for': 'a02-recipient@example.com',
            'secret': 'a02-test-secret',
            'key': 'a02-test-key',
        }
        owner = client.post(f'/api/create-watermark/{doc_id}', json=body, headers=owner_headers)
        print(f'OWNER: HTTP {owner.status_code} {owner.get_json()}')
        assert owner.status_code == 201, 'Owner baseline must succeed before testing authorization'

        other = client.post(f'/api/create-watermark/{doc_id}', json=body, headers=other_headers)
        print(f'NON-OWNER: HTTP {other.status_code} {other.get_json()}')

        engine = app.config['_ENGINE']
        with engine.connect() as conn:
            count = conn.execute(text('SELECT COUNT(*) FROM Versions WHERE documentid = :id'), {'id': doc_id}).scalar_one()
        print(f'Versions created for document: {count}')
        if other.status_code == 201 or count > 1:
            print('CONFIRMED: non-owner created a watermark version (ownership requirement violated).')
        else:
            print('Non-owner did not create a version in this baseline.')
    finally:
        engine = app.config.get('_ENGINE')
        if engine is not None:
            storage_root = Path(app.config['STORAGE_DIR']).resolve()
            if doc_id is not None:
                with engine.begin() as conn:
                    rows = conn.execute(text('SELECT path FROM Versions WHERE documentid = :id'), {'id': doc_id}).fetchall()
                    doc = conn.execute(text('SELECT path FROM Documents WHERE id = :id'), {'id': doc_id}).first()
                    conn.execute(text('DELETE FROM Versions WHERE documentid = :id'), {'id': doc_id})
                    conn.execute(text('DELETE FROM Documents WHERE id = :id'), {'id': doc_id})
                for row in rows:
                    safe_test_file(row.path, storage_root)
                if doc:
                    safe_test_file(doc.path, storage_root)
            if created_users:
                with engine.begin() as conn:
                    for user_id in created_users:
                        conn.execute(text('DELETE FROM Users WHERE id = :id'), {'id': user_id})
        print('Baseline cleanup finished.')

if __name__ == '__main__':
    main()
