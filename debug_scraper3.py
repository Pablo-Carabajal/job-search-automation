import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print('=== COMPUTRABAJO - Estructura completa oferta ===')
r = requests.get('https://ar.computrabajo.com/empleos-en-cordoba-en-san-francisco', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

article = soup.find('article', class_='box_offer')
print('HTML completo del primer article:\n')
print(article.prettify()[:2000])