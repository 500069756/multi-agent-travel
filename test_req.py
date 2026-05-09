import requests
res = requests.post("http://127.0.0.1:8000/api/plan", json={"request": "5-day trip to Paris"})
print(res.status_code)
print(res.text)
