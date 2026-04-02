import json
import logging
import random
from pathlib import Path
from typing import Optional
from core.models import LocalCompany
from core.history_manager import HistoryManager

logger = logging.getLogger(__name__)


class LocalCompanyFallback:
    def __init__(self, db_path: Path, history: Optional[HistoryManager] = None):
        self.history = history
        self.empresas = self._cargar_empresas(db_path)

    def _cargar_empresas(self, path: Path) -> list[LocalCompany]:
        if not path.exists():
            logger.warning(f"Archivo de empresas locales no encontrado: {path}")
            return []
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            empresas = []
            for item in data:
                empresa = LocalCompany(
                    nombre=item.get("nombre", ""),
                    email=item.get("email", ""),
                    rubro=item.get("rubro", ""),
                    direccion=item.get("direccion")
                )
                if empresa.nombre and empresa.email:
                    empresas.append(empresa)
            
            logger.info(f"Cargadas {len(empresas)} empresas locales")
            return empresas
            
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear empresas locales: {e}")
            return []

    def obtener_empresas_habilitadas(self, maximo: int = 10) -> list[LocalCompany]:
        if not self.history:
            random.shuffle(self.empresas)
            return self.empresas[:maximo]
        
        habilitadas = []
        for empresa in self.empresas:
            if self.history.esta_en_cooldown(empresa.nombre):
                logger.debug(f"Empresa en cooldown: {empresa.nombre}")
                continue
            habilitadas.append(empresa)
        
        random.shuffle(habilitadas)
        return habilitadas[:maximo]