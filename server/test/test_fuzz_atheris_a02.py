
import atexit
import io
import sys
import uuid
import atheris
import fitz

from sqlalchemy import text
from server import app
from pathlib import Path

client = app.test_client()
engine = None
owner_id = other_id = doc_id = None
owner_headers = other_headers = None
storage_root = Path(app.config['STORAGE_DIR']).resolve()
counts = {'cases': 0, 'unauthorized_created': 0, 'denied': 0, 'other': 0}
examples = []

def user():
    unique = uuid.uuid4().hex
    data = {'email': f'a02-{unique}@example.com', 'login': f'a02-{unique}', 'password': 'a02-test-password'}
    r = client.post('/api/create-user', json=data)
    assert r.status_code == 201, f'create-user: {r.status_code} {r.get_json()}'
    uid = r.get_json()['id']
    r = client.post('/api/login', json={'email': data['email'], 'password': data['password']})
    assert r.status_code == 200, f'login: {r.status_code} {r.get_json()}'
    return uid, {'Authorization': f'Bearer {r.get_json()["token"]}'}

def safe_remove(path):
    if not path:
        return
    p = Path(path).resolve()
    if p.is_relative_to(storage_root):
        p.unlink(missing_ok=True)

def remove_versions():
    if engine is None or doc_id is None:
        return
    with engine.begin() as conn:
        rows = conn.execute(text('SELECT path FROM Versions WHERE documentid = :id'), {'id': doc_id}).fetchall()
        conn.execute(text('DELETE FROM Versions WHERE documentid = :id'), {'id': doc_id})
    for row in rows:
        safe_remove(row.path)

def cleanup():
    print('\nA-02 final statistics:', counts, flush=True)
    for example in examples:
        print('EXAMPLE:', example, flush=True)
    if engine is None:
        return
    try:
        if doc_id is not None:
            remove_versions()
            with engine.begin() as conn:
                doc = conn.execute(text('SELECT path FROM Documents WHERE id = :id'), {'id': doc_id}).first()
                conn.execute(text('DELETE FROM Documents WHERE id = :id'), {'id': doc_id})
            if doc:
                safe_remove(doc.path)
        with engine.begin() as conn:
            for uid in (owner_id, other_id):
                if uid is not None:
                    conn.execute(text('DELETE FROM Users WHERE id = :id'), {'id': uid})
        print('A-02 cleanup finished.', flush=True)
    except Exception as e:
        print('CLEANUP ERROR:', repr(e), flush=True)

def prepare():
    global owner_id, other_id, owner_headers, other_headers, doc_id, engine
    owner_id, owner_headers = user()
    engine = app.config['_ENGINE']
    other_id, other_headers = user()
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), 'A-02 valid watermark test PDF')
        pdf_bytes = pdf.tobytes()
    upload = client.post('/api/upload-document', headers=owner_headers,
                         data={'file': (io.BytesIO(pdf_bytes), 'a02-fuzz.pdf')})
    assert upload.status_code == 201, f'upload: {upload.status_code} {upload.get_json()}'
    doc_id = upload.get_json()['id']
    body = {'method': 'visible-hmac', 'intended_for': 'baseline@example.com',
            'secret': 'baseline-secret', 'key': 'baseline-key'}
    owner = client.post(f'/api/create-watermark/{doc_id}', json=body, headers=owner_headers)
    assert owner.status_code == 201, f'Owner must succeed first: {owner.status_code} {owner.get_json()}'
    remove_versions()
    print(f'A-02 prepared: document={doc_id}, owner={owner_id}, nonowner={other_id}; owner baseline HTTP 201', flush=True)

def TestOneInput(data):
    if not data:
        return
    fdp = atheris.FuzzedDataProvider(data)
    # Keep a valid method and mostly valid fields so requests reach the vulnerable
    # ownership path instead of being immediately rejected as malformed JSON.
    recipient = fdp.ConsumeUnicodeNoSurrogates(48) or 'recipient@example.com'
    secret = fdp.ConsumeUnicodeNoSurrogates(64) or 'seed-secret'
    key = fdp.ConsumeUnicodeNoSurrogates(64) or 'seed-key'
    position = fdp.PickValueInList([None, None, '', 'center', 'top-left'])
    body = {'method': 'visible-hmac', 'intended_for': recipient, 'secret': secret, 'key': key}
    if position is not None:
        body['position'] = position
    # Both documented ways of specifying document ID (path or JSON).
    if fdp.ConsumeBool():
        url = f'/api/create-watermark/{doc_id}'
    else:
        url = '/api/create-watermark'
        body['id'] = doc_id
    counts['cases'] += 1
    try:
        response = client.post(url, headers=other_headers, json=body)
        with engine.connect() as conn:
            n = conn.execute(text('SELECT COUNT(*) FROM Versions WHERE documentid = :id'), {'id': doc_id}).scalar_one()
        if response.status_code == 201 or n > 0:
            counts['unauthorized_created'] += 1
            if len(examples) < 5:
                examples.append({'case': counts['cases'], 'status': response.status_code,
                                 'versions': n, 'recipient': recipient[:30], 'route': url})
        elif response.status_code in (401, 403, 404):
            counts['denied'] += 1
        else:
            counts['other'] += 1
        if counts['cases'] % 100 == 0:
            print('CHECKPOINT', counts, flush=True)
    finally:
        remove_versions()

if __name__ == '__main__':
    atexit.register(cleanup)
    prepare()

    sys.argv.extend([
        '-max_total_time=60',
        '-max_len=256',
        '-print_final_stats=1',
    ])
    
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()