import requests

login_data = {'username': 'shaaf@gmail.com', 'password': 'password123'}
login_response = requests.post('http://127.0.0.1:8001/api/v1/educators/login', data=login_data)
if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    debug_response = requests.get('http://127.0.0.1:8001/api/v1/students/debug/current-educator', headers=headers)
    print('Debug status:', debug_response.status_code)
    print('Debug data:', debug_response.text)
else:
    print('Login failed:', login_response.text)