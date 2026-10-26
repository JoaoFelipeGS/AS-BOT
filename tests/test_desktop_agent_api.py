import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.routes import (
    DesktopAgentResult,
    claim_desktop_job,
    confirm_publication,
    heartbeat_desktop_job,
    publish_item,
    report_desktop_job_result,
    require_desktop_agent,
)
from backend.config import settings
from backend.models import Base, Fila, Imovel
from backend.schemas import PublishRequest


class DesktopAgentApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _queue_item(self, status="aguardando"):
        imovel = Imovel(
            url="https://example.test/property",
            titulo="Casa de teste",
            preco=300000,
            descricao="Casa com três quartos, dois banheiros e garagem.",
            quartos=3,
            banheiros=2,
            garagem=2,
            imagens_json=["https://cdn.example/photo.jpg"],
        )
        self.db.add(imovel)
        self.db.flush()
        fila = Fila(imovel_id=imovel.id, status=status)
        self.db.add(fila)
        self.db.commit()
        self.db.refresh(fila)
        return fila

    def test_publish_queues_job_and_agent_claims_it_once(self):
        fila = self._queue_item()
        with patch.object(settings, "desktop_agent_token", "test-secret"):
            response = asyncio.run(publish_item(PublishRequest(fila_id=fila.id), self.db, "admin"))

        self.assertEqual(response, {"ok": True, "status": "aguardando_agente"})
        job_response = claim_desktop_job(self.db, _agent=True)
        self.assertEqual(job_response["job"]["fila_id"], fila.id)
        self.assertEqual(
            job_response["job"]["dados_imovel"]["imagens_json"],
            ["https://cdn.example/photo.jpg"],
        )
        self.assertEqual(self.db.get(Fila, fila.id).status, "processando_agente")
        self.assertIsNone(claim_desktop_job(self.db, _agent=True)["job"])

    def test_agent_result_requires_claim_and_prepares_review(self):
        fila = self._queue_item("processando_agente")

        response = report_desktop_job_result(
            fila.id,
            DesktopAgentResult(ready_for_review=True),
            self.db,
            _agent=True,
        )

        self.assertEqual(response["status"], "aguardando_confirmacao")
        self.assertEqual(self.db.get(Fila, fila.id).status, "aguardando_confirmacao")

    def test_heartbeat_keeps_claimed_task_active(self):
        fila = self._queue_item("processando_agente")

        response = heartbeat_desktop_job(fila.id, self.db, _agent=True)

        self.assertTrue(response["ok"])
        self.assertGreaterEqual(self.db.get(Fila, fila.id).atualizado_em, datetime.utcnow() - timedelta(seconds=2))

    def test_claim_marks_orphaned_agent_tasks_as_errors(self):
        fila = self._queue_item("processando_agente")
        fila.atualizado_em = datetime.utcnow() - timedelta(minutes=5)
        self.db.commit()

        response = claim_desktop_job(self.db, _agent=True)

        self.assertIsNone(response["job"])
        self.assertEqual(self.db.get(Fila, fila.id).status, "erro")
        self.assertIn("desconectado", self.db.get(Fila, fila.id).mensagem_erro)

    def test_agent_cannot_report_result_for_unclaimed_queue_item(self):
        fila = self._queue_item()

        with self.assertRaises(HTTPException) as error:
            report_desktop_job_result(
                fila.id,
                DesktopAgentResult(ready_for_review=True),
                self.db,
                _agent=True,
            )

        self.assertEqual(error.exception.status_code, 409)

    def test_failed_agent_job_is_reported_as_error(self):
        fila = self._queue_item("processando_agente")

        response = report_desktop_job_result(
            fila.id,
            DesktopAgentResult(ready_for_review=False, error="Campo não localizado"),
            self.db,
            _agent=True,
        )

        self.assertEqual(response["status"], "erro")
        self.assertEqual(self.db.get(Fila, fila.id).mensagem_erro, "Campo não localizado")

    def test_confirmation_is_rejected_until_agent_prepares_the_item(self):
        fila = self._queue_item("processando_agente")

        with self.assertRaises(HTTPException) as error:
            asyncio.run(confirm_publication(fila.id, self.db, "admin"))

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(self.db.get(Fila, fila.id).status, "processando_agente")

    def test_agent_token_is_required_and_compared(self):
        with patch.object(settings, "desktop_agent_token", "test-secret"):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(require_desktop_agent("Bearer wrong-token"))
            self.assertEqual(error.exception.status_code, 401)
            self.assertTrue(asyncio.run(require_desktop_agent("Bearer test-secret")))

    def test_agent_endpoints_are_disabled_without_server_token(self):
        with patch.object(settings, "desktop_agent_token", ""):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(require_desktop_agent("Bearer any-token"))
        self.assertEqual(error.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
