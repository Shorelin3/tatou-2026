import atexit
import io
import sys
import uuid
import atheris

from collections import Counter
from pathlib import Path

with atheris.instrument_imports():
    import fitz
    from sqlalchemy import text
    from server import app

client = app.test_client()
engine = None
owner_id = other_id = doc_id = None
owner_headers = other_headers = None
storage_root = Path(app.config['STORAGE_DIR']).resolve()
stats = Counter()
examples = []

def create_user():
    unique = uuid.uuid4().hex
    details = {
        'email': f'a02-{unique}@example.com',
        'login': f'a02-{unique}',
        'password': 'a02-test-password'
    }

    response = client.post('/api/create-user', json=details)
    assert response.status_code == 201, (
        response.status_code, response.get_json()
    )

    uid = response.get_json()['id']

    response = client.post(
        '/api/login',
        json={
            'email': details['email'],
            'password': details['password']
        }
    )

    assert response.status_code == 200, (
        response.status_code, response.get_json()
    )

    return uid, {
        'Authorization': f'Bearer {response.get_json()["token"]}'
    }

def remove_file(path):
    if path:
        target = Path(path).resolve()
        if target.is_relative_to(storage_root) and target.is_file():
            target.unlink()

def clear_versions():
    if engine is None or doc_id is None:
        return

    with engine.begin() as conn:
        paths = conn.execute(
            text('SELECT path FROM Versions WHERE documentid=:id'),
            {'id': doc_id}
        ).fetchall()

        conn.execute(
            text('DELETE FROM Versions WHERE documentid=:id'),
            {'id': doc_id}
        )

    for row in paths:
        remove_file(row.path)

def version_count():
    with engine.connect() as conn:
        return conn.execute(
            text('SELECT COUNT(*) FROM Versions WHERE documentid=:id'),
            {'id': doc_id}
        ).scalar_one()

def finish():
    print('\nA-02 EXTENDED FINAL STATISTICS', dict(stats), flush=True)

    for example in examples:
        print('EXAMPLE', example, flush=True)

    if engine is None:
        return

    try:
        if doc_id is not None:
            clear_versions()

            with engine.begin() as conn:
                row = conn.execute(
                    text('SELECT path FROM Documents WHERE id=:id'),
                    {'id': doc_id}
                ).first()

                conn.execute(
                    text('DELETE FROM Documents WHERE id=:id'),
                    {'id': doc_id}
                )

            if row:
                remove_file(row.path)

        with engine.begin() as conn:
            for uid in (owner_id, other_id):
                if uid is not None:
                    conn.execute(
                        text('DELETE FROM Users WHERE id=:id'),
                        {'id': uid}
                    )

        print('A-02 cleanup finished.', flush=True)

    except Exception as exc:
        print('CLEANUP ERROR', repr(exc), flush=True)

def prepare():
    global owner_id, other_id, owner_headers, other_headers, doc_id, engine

    owner_id, owner_headers = create_user()
    engine = app.config['_ENGINE']

    other_id, other_headers = create_user()

    with fitz.open() as pdf:
        pdf.new_page().insert_text((72, 72), 'A-02 extended fuzzing PDF')
        pdf_bytes = pdf.tobytes()

    response = client.post(
        '/api/upload-document',
        headers=owner_headers,
        data={
            'file': (io.BytesIO(pdf_bytes), 'a02-extended.pdf')
        }
    )

    assert response.status_code == 201, (
        response.status_code, response.get_json()
    )

    doc_id = response.get_json()['id']

    body = {
        'method': 'visible-hmac',
        'intended_for': 'baseline@example.com',
        'secret': 'baseline-secret',
        'key': 'baseline-key'
    }

    response = client.post(
        f'/api/create-watermark/{doc_id}',
        json=body,
        headers=owner_headers
    )

    assert response.status_code == 201, (
        'owner control failed',
        response.status_code,
        response.get_json()
    )

    clear_versions()

    print(
        f'Prepared document={doc_id}; owner={owner_id}; '
        f'non-owner={other_id}; owner control HTTP 201',
        flush=True
    )

def fuzz_one(data):
    if not data:
        return

    fdp = atheris.FuzzedDataProvider(data)

    mode = fdp.PickValueInList([
        'owner_valid',
        'nonowner_valid',
        'unauth_valid',
        'owner_invalid',
        'nonowner_invalid',
        'missing_doc'
    ])

    route_type = fdp.ConsumeBool()
    text_value = fdp.ConsumeUnicodeNoSurrogates(60)

    body = {
        'method': 'visible-hmac',
        'intended_for': text_value or 'recipient@example.com',
        'secret': fdp.ConsumeUnicodeNoSurrogates(60) or 'test-secret',
        'key': fdp.ConsumeUnicodeNoSurrogates(60) or 'test-key'
    }

    if fdp.ConsumeBool():
        body['position'] = fdp.PickValueInList([
            '', 'center', 'top-left', None
        ])

    if mode.endswith('invalid'):
        fields = ['method', 'intended_for', 'secret', 'key']
        invalid_values = [None, '', 0, False, [], {}, ['unexpected']]

        # Rotate through all fields, even when Atheris generates
        # very short inputs or repeatedly selects similar cases.
        invalid_index = stats['invalid_cases'] % len(fields)
        field = fields[invalid_index]

        value_index = (
            stats['invalid_cases'] // len(fields)
        ) % len(invalid_values)

        body[field] = invalid_values[value_index]

        stats['invalid_cases'] += 1
        stats[f'invalid_field:{field}'] += 1

    current_id = doc_id + 10000000 if mode == 'missing_doc' else doc_id

    if route_type:
        url = f'/api/create-watermark/{current_id}'
        stats['id_in_path'] += 1
    else:
        url = '/api/create-watermark'
        body['id'] = current_id
        stats['id_in_json'] += 1

    headers = (
        other_headers if mode.startswith('nonowner')
        else {} if mode == 'unauth_valid'
        else owner_headers
    )

    stats['cases'] += 1
    stats[f'mode:{mode}'] += 1

    try:
        response = client.post(
            url,
            headers=headers,
            json=body
        )

        n = version_count()
        status = response.status_code

        stats[f'http:{status}'] += 1
        stats[f'{mode}:http:{status}'] += 1

        violation = False

        if mode == 'owner_valid':
            if status == 201 and n == 1:
                stats['owner_valid_success'] += 1
            else:
                stats['owner_valid_unexpected'] += 1

        elif mode.startswith('nonowner') or mode == 'unauth_valid':
            if n > 0 or status == 201:
                stats['unauthorized_creation'] += 1
                violation = True
            else:
                stats['unauthorized_denied'] += 1

        elif mode == 'missing_doc' and n > 0:
            stats['missing_doc_created_version'] += 1
            violation = True

        if status >= 500:
            stats['http_5xx'] += 1

            if stats['http_5xx'] <= 3:
                print(
                    "HTTP_5XX_EXAMPLE",
                    {
                        "mode": mode,
                        "status": status,
                        "body": repr(body),
                        "response": response.get_data(as_text=True)[:300]
                    },
                    flush=True
                )

        if (
            violation
            or status >= 500
            or (
                mode == 'owner_valid'
                and (status != 201 or n != 1)
            )
        ) and len(examples) < 12:
            examples.append({
                'case': stats['cases'],
                'mode': mode,
                'status': status,
                'versions': n,
                'body': repr(body)[:220],
                'response': response.get_data(as_text=True)[:180]
            })

        if stats['cases'] % 500 == 0:
            print(
                'CHECKPOINT',
                stats['cases'],
                dict(stats),
                flush=True
            )

    finally:
        clear_versions()

if __name__ == '__main__':
    atexit.register(finish)
    prepare()

    defaults = {
        'max_total_time': '60',
        'max_len': '256',
        'print_final_stats': '1'
    }

    for option, value in defaults.items():
        if not any(
            arg.startswith(f'-{option}=')
            for arg in sys.argv[1:]
        ):
            sys.argv.append(f'-{option}={value}')

    atheris.Setup(sys.argv, fuzz_one)
    atheris.Fuzz()
