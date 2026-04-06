import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print('=== BUMERAN ===')
r = requests.get('https://www.bumeran.com.ar/en-cordoba/san-francisco/empleos.html', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')
print('Título:', soup.title.string if soup.title else 'Sin título')

articles = soup.find_all(class_=True)
classes = set()
for tag in soup.find_all(class_=True):
    for c in tag.get('class', []):
        classes.add(c)
print('Clases únicas:')
for c in sorted(classes)[:20]:
    print(f'  {c}')

article = soup.find('article')
if article:
    print('\nPrimer article:')
    print(article.prettify()[:1000])