import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print('=== COMPUTRABAJO ===')
r = requests.get('https://ar.computrabajo.com/empleos-en-cordoba-en-san-francisco', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
print('Título página:', soup.title.string if soup.title else 'Sin título')

articles = soup.find_all('article')
print(f'Articles encontrados: {len(articles)}')

print('Clases únicas encontradas:')
classes = set()
for tag in soup.find_all(class_=True):
    for c in tag.get('class', []):
        classes.add(c)
for c in sorted(classes)[:30]:
    print(f'  {c}')