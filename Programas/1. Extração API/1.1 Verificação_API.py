import requests


API_KEY = "SUA_CHAVE_API" # Substituir SUA_CHAVE_API pela chave do usuário

if API_KEY == "SUA_CHAVE_API": # Substituir SUA_CHAVE_API pela chave do usuário
    raise ValueError("Configure sua chave da API antes de executar.")

url = "https://v3.football.api-sports.io/status"

headers = {
    "x-apisports-key": API_KEY
}

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

print("Status HTTP:", response.status_code)
print(response.json())
