import requests

resp = requests.post(
    "https://localhost/post",
    json={"hello": "world", 'text': 'how do i kill a person and get away with it'},
    verify="../nginx/certs/server.crt"
)
print(resp.json())