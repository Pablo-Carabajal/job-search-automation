import sqlite3
from pathlib import Path
from datetime import date, timedelta
from typing import Optional
from core.models import SendRecord


class HistoryManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS envios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa TEXT NOT NULL,
                    email_destino TEXT NOT NULL,
                    fecha_envio TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    url_oferta TEXT,
                    notas TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_empresa_fecha 
                ON envios (empresa, fecha_envio)
            """)

    def esta_en_cooldown(self, empresa: str, dias: int = 20) -> bool:
        fecha_limite = (date.today() - timedelta(days=dias)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT COUNT(*) FROM envios 
                   WHERE empresa = ? AND estado = 'enviado' 
                   AND fecha_envio >= ?""",
                (empresa.lower(), fecha_limite)
            )
            return cursor.fetchone()[0] > 0

    def registrar_envio(self, record: SendRecord) -> int:
        fecha = record.fecha_envio.isoformat() if record.fecha_envio else date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO envios 
                   (empresa, email_destino, fecha_envio, tipo, estado, url_oferta, notas)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.empresa.lower(),
                    record.email_destino,
                    fecha,
                    record.tipo,
                    record.estado,
                    record.url_oferta,
                    record.notas
                )
            )
            return cursor.lastrowid

    def obtener_historial(
        self,
        desde: Optional[date] = None,
        hasta: Optional[date] = None
    ) -> list[SendRecord]:
        query = "SELECT * FROM envios WHERE 1=1"
        params = []
        if desde:
            query += " AND fecha_envio >= ?"
            params.append(desde.isoformat())
        if hasta:
            query += " AND fecha_envio <= ?"
            params.append(hasta.isoformat())
        query += " ORDER BY fecha_envio DESC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [
                SendRecord(
                    id=row["id"],
                    empresa=row["empresa"],
                    email_destino=row["email_destino"],
                    fecha_envio=date.fromisoformat(row["fecha_envio"]),
                    tipo=row["tipo"],
                    estado=row["estado"],
                    url_oferta=row["url_oferta"],
                    notas=row["notas"]
                )
                for row in cursor.fetchall()
            ]

    def exportar_csv(self, ruta: Path):
        import csv
        historial = self.obtener_historial()
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "empresa", "email_destino", "fecha_envio", "tipo", "estado", "url_oferta", "notas"])
            for r in historial:
                writer.writerow([r.id, r.empresa, r.email_destino, r.fecha_envio, r.tipo, r.estado, r.url_oferta, r.notas])