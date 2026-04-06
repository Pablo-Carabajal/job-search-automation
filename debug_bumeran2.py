import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
}

r = requests.get('https://www.bumeran.com.ar/en-cordoba/san-francisco/empleos.html', headers=headers, timeout=15)
print(f'Status: {r.status_code}')
print(f'Longitud respuesta: {len(r.text)}')
print('Primeras 2000 chars:')
print(r.text[:2000])