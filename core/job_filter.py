import logging
from pathlib import Path
from typing import Optional
from core.models import JobOffer
from core.history_manager import HistoryManager

logger = logging.getLogger(__name__)


class JobFilter:
    def __init__(self, history: HistoryManager, blacklist_path: Path):
        self.history = history
        self.blacklist = self._cargar_blacklist(blacklist_path)
        self.cooldown_dias = 20

    def _cargar_blacklist(self, path: Path) -> set[str]:
        if not path.exists():
            logger.warning(f"Blacklist no encontrada: {path}")
            return set()
        
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        logger.info(f"Blacklist cargada: {len(lines)} empresas")
        return set(lines)

    def filtrar(self, ofertas: list[JobOffer], categorias_permitidas: Optional[list[str]] = None) -> list[JobOffer]:
        filtradas = []
        
        for oferta in ofertas:
            if self._en_blacklist(oferta.empresa):
                logger.debug(f"Descartada (blacklist): {oferta.empresa}")
                continue
            
            # Si la empresa es conocida, aplicar cooldown por nombre de empresa
            # Si no, usar el ID de la oferta para no bloquear otras ofertas sin nombre
            clave_cooldown = oferta.empresa if oferta.empresa != "desconocida" else oferta.id
            if self.history.esta_en_cooldown(clave_cooldown, self.cooldown_dias):
                logger.debug(f"Descartada (cooldown): {clave_cooldown}")
                continue
            
            if categorias_permitidas and oferta.categoria:
                if not self._cumple_categoria(oferta.categoria, categorias_permitidas):
                    logger.debug(f"Descartada (categoría): {oferta.categoria}")
                    continue
            
            filtradas.append(oferta)
        
        logger.info(f"Ofertas filtradas: {len(filtradas)}/{len(ofertas)}")
        return filtradas

    def _en_blacklist(self, empresa: str) -> bool:
        empresa_lower = empresa.lower().strip()
        
        for item in self.blacklist:
            item_lower = item.lower().strip()
            if item_lower in empresa_lower:
                return True
        
        return False

    def _cumple_categoria(self, categoria: str, permitidas: list[str]) -> bool:
        categoria_lower = categoria.lower()
        
        for perm in permitidas:
            perm_lower = perm.lower()
            if perm_lower in categoria_lower or categoria_lower in perm_lower:
                return True
        
        return False