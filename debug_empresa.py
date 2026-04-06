import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get('https://ar.computrabajo.com/empleos-en-cordoba-en-san-francisco', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

article = soup.find('article', class_='box_offer')
print('=== Estructura empresa ===')
# Buscar todos los elementos a
for a in article.find_all('a'):
    href = a.get('href', '')
    text = a.get_text(strip=True)
    classes = a.get('class', [])
    print(f"  <a> clases: {classes}, href: {href[:50]}, texto: {text[:40]}")