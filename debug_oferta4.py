import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get('https://ar.computrabajo.com/empleos-en-cordoba-en-san-francisco', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

articles = soup.find_all('article', class_='box_offer')

# Oferta 4 y 5
for i, article in enumerate([articles[3], articles[4]]):
    print(f"\n=== Oferta {i+4} ===")
    links = article.find_all("a")
    for a in links:
        href = a.get("href", "")
        text = a.get_text(strip=True)[:50]
        clases = a.get("class", [])
        print(f"  clases: {clases}")
        print(f"  href: {href[:60]}, texto: {text}")