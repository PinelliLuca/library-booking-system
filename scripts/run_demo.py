import requests
r = requests.post("http://localhost:5000/demo/run-scenario")
print(r.status_code)