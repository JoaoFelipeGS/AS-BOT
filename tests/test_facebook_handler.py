import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from backend.services import facebook_handler


class FacebookPublishFailureTests(unittest.IsolatedAsyncioTestCase):
    async def test_photo_upload_uses_download_and_validation_utilities(self):
        locator = SimpleNamespace(
            first=None,
            wait_for=AsyncMock(),
            evaluate=AsyncMock(),
            set_input_files=AsyncMock(),
        )
        locator.first = locator
        page = SimpleNamespace(locator=lambda _selector: locator)

        def download_image(_image_url, destination):
            with open(destination, "wb") as image_file:
                image_file.write(b"image")
            return True

        with (
            patch.object(facebook_handler.utils, "baixar_imagem", side_effect=download_image) as download,
            patch.object(facebook_handler.utils, "validar_imagem", return_value=True) as validate,
        ):
            result = await facebook_handler._upload_imagens_por_referencia(
                page,
                ["https://example.test/photo.jpg"],
                imovel_id=36,
            )

        self.assertTrue(result)
        download.assert_called_once()
        validate.assert_called_once()
        locator.set_input_files.assert_awaited_once()

    async def test_photo_upload_failure_does_not_report_publish_ready(self):
        page = SimpleNamespace(goto=AsyncMock())

        with (
            patch.object(facebook_handler.asyncio, "sleep", new=AsyncMock()),
            patch.object(
                facebook_handler,
                "_upload_imagens_por_referencia",
                new=AsyncMock(return_value=False),
            ),
            patch.object(facebook_handler, "_achar_input_original", new=AsyncMock()) as find_input,
        ):
            result = await facebook_handler.publicar_imovel(
                page,
                imovel_id=36,
                fila_id=1,
                dados_imovel={"imagens_json": ["https://example.test/photo.jpg"]},
            )

        self.assertFalse(result)
        find_input.assert_not_awaited()

    async def test_missing_description_field_does_not_report_publish_ready(self):
        field = object()
        description = SimpleNamespace(wait_for=AsyncMock(side_effect=TimeoutError()))
        page = SimpleNamespace(
            goto=AsyncMock(),
            locator=lambda _selector: SimpleNamespace(last=description),
        )

        with (
            patch.object(facebook_handler.asyncio, "sleep", new=AsyncMock()),
            patch.object(
                facebook_handler,
                "_upload_imagens_por_referencia",
                new=AsyncMock(return_value=True),
            ),
            patch.object(
                facebook_handler,
                "_achar_input_original",
                new=AsyncMock(return_value=field),
            ),
            patch.object(
                facebook_handler,
                "_type_original_fixed",
                new=AsyncMock(return_value=True),
            ),
            patch.object(
                facebook_handler,
                "_simular_f12_console",
                new=AsyncMock(),
            ) as show_next_step,
        ):
            result = await facebook_handler.publicar_imovel(
                page,
                imovel_id=36,
                fila_id=1,
                dados_imovel={
                    "imagens_json": ["https://example.test/photo.jpg"],
                    "preco": 300000,
                    "quartos": 3,
                    "banheiros": 2,
                    "descricao": "Casa com três quartos, dois banheiros e garagem.",
                },
            )

        self.assertFalse(result)
        show_next_step.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
