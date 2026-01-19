import requests

resp = requests.post(
    "https://localhost/post",
    json={"hello": "world"},
    verify="../nginx/certs/server.crt"
    # verify=False
)

print(resp.status_code)
print(resp.json())
