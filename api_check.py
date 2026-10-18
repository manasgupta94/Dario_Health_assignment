import urllib.request

urls = [
    'https://api.open-meteo.com/v1/forecast?latitude=51.5072&longitude=-0.1276&current=temperature_2m,weather_code&hourly=temperature_2m',
    'https://site.api.espn.com/apis/site/v2/sports/cricket/scoreboard',
    'https://api.cricapi.com/v1/currentMatches?apikey=demo&offset=0',
]

for url in urls:
    print('URL:', url)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(500).decode('utf-8', 'ignore')
            print('STATUS: OK')
            print('HTTP:', resp.status)
            print(body[:250].replace('\n', ' '))
    except Exception as e:
        print('STATUS: ERROR')
        print(type(e).__name__, e)
    print('-' * 80)
