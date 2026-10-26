import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import requests

from backend.desktop_agent import _wait_for_operator_confirmation


class DesktopAgentConfirmationTests(unittest.IsolatedAsyncioTestCase):
    async def test_wait_stops_when_task_was_deleted(self):
        error = requests.HTTPError()
        error.response = SimpleNamespace(status_code=404)
        client = SimpleNamespace(request=AsyncMock(side_effect=error))

        await _wait_for_operator_confirmation(client, fila_id=12)

        client.request.assert_awaited_once()

    async def test_wait_stops_when_api_rejects_agent_authentication(self):
        error = requests.HTTPError()
        error.response = SimpleNamespace(status_code=401)
        client = SimpleNamespace(request=AsyncMock(side_effect=error))

        with self.assertRaisesRegex(RuntimeError, "recusou a autenticação"):
            await _wait_for_operator_confirmation(client, fila_id=12)

        client.request.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
