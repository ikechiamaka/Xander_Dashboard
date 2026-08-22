import requests
import json
from datetime import datetime

url = "https://mocoapi.azure-api.net/sheriff/logs/v1/GetDailyLog"
headers = {
    "Ocp-Apim-Subscription-Key": "9139f54342304125a9672fdcbd9c327e",
    "Origin": "https://www.countyofmonterey.gov",
    "Referer": "https://www.countyofmonterey.gov/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
print(response.status_code)

data = response.json()
print(json.dumps(data, indent=2)[:1000])  # peek at structure first