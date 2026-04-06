import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print('=== COMPUTRABAJO - Extracción detallada ===')
r = requests.get('https://ar.computrabajo.com/empleos-en-cordoba-en-san-francisco', headers=headers, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

articles = soup.find_all('article')
print(f'Total articles: {len(articles)}')

for i, article in enumerate(articles[:3]):
    print(f'\n--- Oferta {i+1} ---')
    print(f'Classes: {article.get("class")}')
    
    # Buscar título
    titulo = article.find('h2')
    if titulo:
        print(f'Título: {titulo.get_text(strip=True)}')
        a = titulo.find('a')
        if a:
            print(f'  URL: {a.get("href")}')
    
    # Buscar empresa
    empresa = article.find(class_=lambda x: x and ('empresa' in x.lower() or 'company' in x.lower()) if x else False)
    if not empresa:
        # Buscar por span o cualquier clase que contenga empresa
        spans = article.find_all('span')
        for s in spans:
            if 'empresa' in str(s.get('class', [])).lower():
                empresa = s
                break
    print(f'Empresa: {empresa.get_text(strip=True) if empresa else "No encontrada"}')
    
    # Buscar fecha
    fecha = article.find('time')
    if not fecha:
        fecha = article.find(class_=lambda x: x and 'date' in x.lower() if x else False)
    print(f'Fecha: {fecha.get_text(strip=True) if fecha else "No encontrada"}')
    
    # Buscar ubicación
    ubicacion = article.find(class_=lambda x: x and 'ubicacion' in x.lower() if x else False)
    print(f'Ubicación: {ubicacion.get_text(strip=True) if ubicacion else "No encontrada"}')
    
    print(f'HTML preview: {str(article)[:500]}...')