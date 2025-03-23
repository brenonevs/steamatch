import requests

url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
params = {'key': '9E61CF132D7355A5D1CB171BED5E6FDC'}
response = requests.get(url, params=params, timeout=10) 

print(response.json())