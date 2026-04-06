import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get('https://ar.computrabajo.com/empleos-en-cordoba-en-san-francisco', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

articles = soup.find_all('article', class_='box_offer')

# Oferta 2 y 3
for i, article in enumerate([articles[1], articles[2]]):
    print(f"\n=== Oferta {i+2} ===")
    print(f"HTML: {article}")
    break