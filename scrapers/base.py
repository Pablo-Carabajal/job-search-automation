from abc import ABC, abstractmethod
from typing import Optional
import requests
import logging
import time
import random

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self, ciudad: str = "San Francisco", provincia: str = "Córdoba"):
        self.ciudad = ciudad
        self.provincia = provincia
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
        }

    @abstractmethod
    def scrape(self) -> list:
        pass

    def _delay(self, min_sec: float = 2, max_sec: float = 5):
        tiempo = random.uniform(min_sec, max_sec)
        logger.debug(f"Esperando {tiempo:.1f}s...")
        time.sleep(tiempo)

    def _get(self, url: str, retries: int = 2) -> Optional["requests.Response"]:
        import requests
        for intento in range(retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                return response
            except Exception as e:
                logger.warning(f"Error en request a {url} (intento {intento+1}/{retries}): {e}")
                if intento < retries - 1:
                    time.sleep(5)
        return None