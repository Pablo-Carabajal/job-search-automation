import sys
sys.path.insert(0, '.')
from scrapers.computrabajo import ScraperComputrabajo

scraper = ScraperComputrabajo()
ofertas = scraper.scrape()
print(f"\nTotal ofertas encontradas: {len(ofertas)}")
for i, o in enumerate(ofertas[:5]):
    print(f"\n--- Oferta {i+1} ---")
    print(f"Título: {o.titulo}")
    print(f"Empresa: {o.empresa}")
    print(f"URL: {o.url_oferta}")