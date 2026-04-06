import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print('=== ZONAJOBS ===')
r = requests.get('https://www.zonajobs.com.ar/en-cordoba/san-francisco/empleos.html', headers=headers, timeout=15)
print(f'Status: {r.status_code}')
print(f'Longitud: {len(r.text)}')

# Buscar contenido de ofertas
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, 'html.parser')

# Ver si hay ofertas en el HTML
articles = soup.find_all('article')
print(f'Articles: {len(articles)}')

# Buscar ofertas
offers = soup.find_all(class_=lambda x: x and 'offer' in str(x).lower() if x else False)
print(f'Ofertas (offer): {len(offers)}')

# Ver estructura
print('Primeras clases:')
classes = set()
for tag in soup.find_all(class_=True)[:30]:
    for c in tag.get('class', []):
        classes.add(c)
for c in sorted(classes)[:15]:
    print(f'  {c}')