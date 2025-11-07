import json
import urllib.request
import urllib.error

def post_json(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.getcode(), resp.read().decode()
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
        except Exception:
            body = ''
        return e.code, body
    except Exception as e:
        return None, str(e)

if __name__ == '__main__':
    base = 'http://127.0.0.1:8003'
    print('Health check:')
    try:
        import urllib.request
        with urllib.request.urlopen(base + '/health', timeout=5) as r:
            print(r.read().decode())
    except Exception as e:
        print('Health error:', e)

    reg_payload = {
        'email': 'test.teacher.ai+automation@example.com',
        'first_name': 'Auto',
        'last_name': 'Tester',
        'password': 'Password123!'
    }
    code, body = post_json(base + '/api/v1/educators/register', reg_payload)
    print('\nRegister response:', code)
    print(body)

    # Try login via urllib (form-encoded)
    import urllib.parse
    login_data = urllib.parse.urlencode({'username': reg_payload['email'], 'password': reg_payload['password']}).encode()
    req = urllib.request.Request(base + '/api/v1/educators/login', data=login_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            login_body = r.read().decode()
            print('\nLogin response: 200')
            print(login_body)
            login_json = json.loads(login_body)
            token = login_json.get('access_token')
    except urllib.error.HTTPError as e:
        try:
            print('\nLogin failed:', e.code, e.read().decode())
        except:
            print('\nLogin failed:', e)
        token = None
    except Exception as e:
        print('\nLogin error:', e)
        token = None

    if not token:
        print('\nCannot continue without token')
        raise SystemExit(1)

    # Fetch one student
    try:
        req = urllib.request.Request(base + '/api/v1/students?limit=1', headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req, timeout=10) as r:
            students = json.loads(r.read().decode())
            print('\nStudents:', students)
            if isinstance(students, list) and len(students) > 0:
                sid = students[0]['id']
            elif isinstance(students, dict):
                sid = students.get('id')
            else:
                sid = None
    except Exception as e:
        print('\nError fetching students:', e)
        sid = None

    if not sid:
        print('\nNo student found to send to')
        raise SystemExit(1)

    # Send message
    msg_payload = {
        'receiver_id': sid,
        'receiver_type': 'student',
        'subject': 'Automated test message',
        'message': 'Hello from automated test',
        'message_type': 'general',
        'priority': 'normal',
        'is_report': False
    }
    code, body = post_json(base + '/api/v1/messages/send', msg_payload)
    print('\nSend message response:', code)
    print(body)
