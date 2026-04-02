import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import os

from core.models import JobOffer, SendRecord
from core.history_manager import HistoryManager
from core.job_filter import JobFilter


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        os.unlink(db_path)


@pytest.fixture
def temp_blacklist():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("ZF Sachs S.A.\n")
        f.write("zf sachs\n")
        f.write("empresa bloqueada\n")
        blacklist_path = Path(f.name)
    yield blacklist_path
    if blacklist_path.exists():
        os.unlink(blacklist_path)


@pytest.fixture
def history(temp_db):
    return HistoryManager(temp_db)


class TestHistoryManager:
    def test_registrar_envio(self, history):
        record = SendRecord(
            empresa="Test empresa",
            email_destino="test@test.com",
            fecha_envio=date.today(),
            tipo="oferta_portal",
            estado="enviado"
        )
        id_registro = history.registrar_envio(record)
        assert id_registro is not None
        assert id_registro > 0

    def test_esta_en_cooldown_sin_envios(self, history):
        assert not history.esta_en_cooldown("Empresa X", dias=20)

    def test_esta_en_cooldown_con_envio_reciente(self, history):
        record = SendRecord(
            empresa="Empresa reciente",
            email_destino="test@test.com",
            fecha_envio=date.today(),
            tipo="oferta_portal",
            estado="enviado"
        )
        history.registrar_envio(record)
        assert history.esta_en_cooldown("Empresa reciente", dias=20)

    def test_esta_en_cooldown_sin_envio_reciente(self, history):
        record = SendRecord(
            empresa="Empresa antigua",
            email_destino="test@test.com",
            fecha_envio=date.today() - timedelta(days=30),
            tipo="oferta_portal",
            estado="enviado"
        )
        history.registrar_envio(record)
        assert not history.esta_en_cooldown("Empresa antigua", dias=20)

    def test_esta_en_cooldown_case_insensitive(self, history):
        record = SendRecord(
            empresa="EMPRESA TEST",
            email_destino="test@test.com",
            fecha_envio=date.today(),
            tipo="oferta_portal",
            estado="enviado"
        )
        history.registrar_envio(record)
        assert history.esta_en_cooldown("empresa test", dias=20)
        assert history.esta_en_cooldown("EMPRESA TEST", dias=20)


class TestJobFilter:
    def test_filtrar_sin_blacklist(self, temp_blacklist, history):
        filtro = JobFilter(history, temp_blacklist)
        ofertas = [
            JobOffer(
                id="1",
                titulo="Puesto 1",
                empresa="Empresa buena",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test"
            )
        ]
        result = filtro.filtrar(ofertas)
        assert len(result) == 1

    def test_filtrar_con_blacklist(self, temp_blacklist, history):
        filtro = JobFilter(history, temp_blacklist)
        ofertas = [
            JobOffer(
                id="1",
                titulo="Puesto 1",
                empresa="ZF Sachs S.A.",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test"
            )
        ]
        result = filtro.filtrar(ofertas)
        assert len(result) == 0

    def test_filtrar_cooldown(self, temp_blacklist, history):
        filtro = JobFilter(history, temp_blacklist)
        
        record = SendRecord(
            empresa="Empresa cooldown",
            email_destino="test@test.com",
            fecha_envio=date.today(),
            tipo="oferta_portal",
            estado="enviado"
        )
        history.registrar_envio(record)
        
        ofertas = [
            JobOffer(
                id="1",
                titulo="Puesto 1",
                empresa="Empresa cooldown",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test"
            )
        ]
        result = filtro.filtrar(ofertas)
        assert len(result) == 0

    def test_filtrar_empresa_desconocida_no_cooldown_por_nombre(self, temp_blacklist, history):
        filtro = JobFilter(history, temp_blacklist)
        
        ofertas = [
            JobOffer(
                id="123",
                titulo="Puesto 1",
                empresa="desconocida",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test"
            )
        ]
        result = filtro.filtrar(ofertas)
        assert len(result) == 1

    def test_filtrar_categorias(self, temp_blacklist, history):
        filtro = JobFilter(history, temp_blacklist)
        
        ofertas = [
            JobOffer(
                id="1",
                titulo="Puesto producción",
                empresa="Empresa 1",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test",
                categoria="Producción / Operarios"
            ),
            JobOffer(
                id="2",
                titulo="Puesto ventas",
                empresa="Empresa 2",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test",
                categoria="Ventas"
            ),
            JobOffer(
                id="3",
                titulo="PuestoTI",
                empresa="Empresa 3",
                email_contacto="email@empresa.com",
                url_oferta="http://test.com",
                portal_origen="test",
                fecha_publicacion=date.today(),
                descripcion="",
                ciudad="Test",
                categoria="Informática"
            )
        ]
        
        categorias = ["Producción / Operarios / Manufactura", "Administración / Oficina", "Almacén / Logística / Transporte", "Ventas"]
        result = filtro.filtrar(ofertas, categorias)
        
        assert len(result) == 2
        assert result[0].empresa == "Empresa 1"
        assert result[1].empresa == "Empresa 2"