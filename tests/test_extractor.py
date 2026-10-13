import unittest

from bs4 import BeautifulSoup

from backend.services.extractor import _extrair_fotos, _localizar_galerias
from backend.services.extractor_service import _reformulacao_preserva_descricao


class _UnexpectedPageAccess:
    async def query_selector_all(self, selector):
        raise AssertionError(f"Gallery was already found in parsed HTML: {selector}")


class PropertyPhotoExtractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_gilmar_lazy_carousel_uses_slide_urls_not_loader_or_agent_photo(self):
        soup = BeautifulSoup(
            """
            <div class="f-carousel">
              <div class="f-carousel__slide" href="https://cdn.example/property-1.jpeg" data-fancybox="gallery">
                <img src="/media/image-loader.gif" onload="this.src='https://cdn.example/property-1.jpeg'">
              </div>
              <div class="f-carousel__slide" href="https://cdn.example/property-2.jpeg" data-fancybox="gallery">
                <img src="/media/image-loader.gif">
              </div>
            </div>
            <div class="agent-card"><img src="https://cdn.example/agent.jpeg"></div>
            <meta property="og:image" content="https://cdn.example/social-preview.jpeg">
            """,
            "lxml",
        )

        photos = await _extrair_fotos(
            _UnexpectedPageAccess(),
            soup,
            "https://agency.example/property/1",
        )

        self.assertEqual(
            photos,
            [
                "https://cdn.example/property-1.jpeg",
                "https://cdn.example/property-2.jpeg",
            ],
        )

    async def test_vavence_picture_prefers_medium_source_and_deduplicates_carousel_clones(self):
        soup = BeautifulSoup(
            """
            <section class="property-gallery-row">
              <div class="owl-carousel">
                <div class="item">
                  <picture>
                    <source data-md-src="https://cdn.example/home-1_md.webp"
                            srcset="https://cdn.example/home-1_sm.webp">
                    <img src="https://cdn.example/home-1_sm.jpg">
                  </picture>
                </div>
                <div class="item">
                  <picture>
                    <source data-md-src="https://cdn.example/home-2_md.webp">
                    <img src="https://cdn.example/home-2_sm.jpg">
                  </picture>
                </div>
                <div class="item cloned">
                  <picture>
                    <source data-md-src="https://cdn.example/home-1_md.webp">
                    <img src="https://cdn.example/home-1_sm.jpg">
                  </picture>
                </div>
              </div>
            </section>
            <div class="broker-card"><img src="https://cdn.example/broker.webp"></div>
            """,
            "lxml",
        )

        photos = await _extrair_fotos(
            _UnexpectedPageAccess(),
            soup,
            "https://agency.example/property/1",
        )

        self.assertEqual(
            photos,
            [
                "https://cdn.example/home-1_md.webp",
                "https://cdn.example/home-2_md.webp",
            ],
        )

    async def test_styled_gallery_wrapper_is_recognized_without_collecting_agent_photo(self):
        soup = BeautifulSoup(
            """
            <div class="dMbhrh">
              <div class="WrapperImage"><img src="https://cdn.example/room-1.jpg"></div>
              <div class="WrapperImage"><img src="https://cdn.example/room-2.jpg"></div>
            </div>
            <div class="broker-card"><img src="https://cdn.example/broker.jpg"></div>
            """,
            "lxml",
        )

        photos = await _extrair_fotos(
            _UnexpectedPageAccess(),
            soup,
            "https://agency.example/property/1",
        )

        self.assertEqual(
            photos,
            [
                "https://cdn.example/room-1.jpg",
                "https://cdn.example/room-2.jpg",
            ],
        )

    def test_gallery_locator_ignores_recommendation_carousels(self):
        soup = BeautifulSoup(
            """
            <div class="related-carousel gallery">
              <img src="https://cdn.example/other-property.jpg">
            </div>
            <div class="f-carousel">
              <div class="f-carousel__slide" href="https://cdn.example/listing.jpg"
                   data-fancybox="gallery">
                <img src="/media/image-loader.gif">
              </div>
            </div>
            """,
            "lxml",
        )

        roots = _localizar_galerias(soup)

        self.assertEqual(len(roots), 1)
        self.assertIn("f-carousel", roots[0].get("class", []))


class DescriptionReformulationTests(unittest.TestCase):
    def test_rejects_materially_shortened_reformulation(self):
        original = "Casa com cozinha planejada, lavanderia, área gourmet e garagem coberta para dois carros."
        shortened = "Casa com ambientes planejados e garagem."

        self.assertFalse(_reformulacao_preserva_descricao(original, shortened))

    def test_accepts_reformulation_that_keeps_similar_content_length(self):
        original = "Casa com cozinha planejada, lavanderia, área gourmet e garagem coberta para dois carros."
        reformulated = "Casa com cozinha planejada e lavanderia, área gourmet completa e garagem coberta para dois veículos."

        self.assertTrue(_reformulacao_preserva_descricao(original, reformulated))
