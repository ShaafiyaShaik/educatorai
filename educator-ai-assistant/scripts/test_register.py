import json,urllib.request,urllib.error
url='http://127.0.0.1:8003/api/v1/educators/register'
data=json.dumps({"email":"test.teacher@school.com","first_name":"Test","last_name":"Teacher","password":"TestPass123!"}).encode('utf-8')
req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'})
try:
    resp=urllib.request.urlopen(req, timeout=10)
    print('STATUS', resp.getcode())
    print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('HTTP_ERROR', e.code)
    try:
        body=e.read().decode()
        print(body)
    except:
        pass
except Exception as e:
    print('ERROR', str(e))
