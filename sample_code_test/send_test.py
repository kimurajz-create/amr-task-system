import requests
data = {
    "name": "Jordan",
    "score": 95
}

response = requests.post("http://localhost:3000/upload", json=data)

print("伺服器回應：", response.json())
