import unittest

from bs4 import BeautifulSoup

from backend.services.extractor import (
    _deduplicar_fotos,
    _extrair_descricao,
    _extrair_fotos,
    _extrair_fotos_premier,
    _localizar_galerias,
)
from backend.services.extractor_service import _reformulacao_preserva_descricao


class _UnexpectedPageAccess:
    async def query_selector_all(self, selector):
        raise AssertionError(f"Gallery was already found in parsed HTML: {selector}")


class _UnionApiPage:
    async def evaluate(self, script):
        return [
            f"https://cdn.example/property/photo-{index}.jpg"
            for index in range(1, 13)
        ]

    async def query_selector_all(self, selector):
        raise AssertionError(f"The trusted listing API already supplied photos: {selector}")


class PropertyPhotoExtractionTests(unittest.IsolatedAsyncioTestCase):
    async def test_as_uses_expanded_listing_gallery_and_ignores_thumbnails_and_other_assets(self):
        property_id = "5ca71910-06e5-4109-900e-2adbf7d5abc0"
        images = "".join(
            f'<img src="https://images.example/properties/{property_id}/images/{index}.jpg">'
            for index in range(1, 11)
        )
        thumbnails = "".join(
            f'<img src="https://images.example/properties/{property_id}/images/600x450/outside/{index}.webp">'
            for index in range(1, 7)
        )
        soup = BeautifulSoup(
            f"""
            <div class="Detail__gallery">
              <img src="https://images.example/properties/{property_id}/images/1.jpg">
              <img src="https://images.example/properties/{property_id}/images/2.jpg">
              <img src="https://images.example/properties/{property_id}/images/3.jpg">
            </div>
            <div class="ReactModal__Content">
              {images}{thumbnails}
              <img src="https://images.example/users/broker.jpg">
              <img src="https://images.example/properties/other-property/images/related.jpg">
            </div>
            """,
            "lxml",
        )

        photos = await _extrair_fotos(
            _UnexpectedPageAccess(),
            soup,
            "https://asimobiliaria.com/imovel/184521",
        )

        self.assertEqual(len(photos), 10)
        self.assertTrue(all(f"/properties/{property_id}/images/" in photo for photo in photos))
        self.assertFalse(any("600x450" in photo for photo in photos))

    async def test_uniao_uses_property_api_images_instead_of_partial_dom_gallery(self):
        soup = BeautifulSoup(
            """
            <div class="property-gallery">
              <img src="https://cdn.example/cover.jpg">
            </div>
            """,
            "lxml",
        )

        photos = await _extrair_fotos(
            _UnionApiPage(),
            soup,
            "https://www.imobiliariauniao.com.br/imovel/32596?from=%2F",
        )

        self.assertEqual(len(photos), 12)
        self.assertEqual(photos[0], "https://cdn.example/property/photo-1.jpg")

    def test_vavence_alternate_formats_and_responsive_sizes_share_asset_identity(self):
        photos = _deduplicar_fotos(
            [
                "https://cdn.example/album/photo-1_md.webp",
                "https://cdn.example/album/photo-1_md.jpg",
                "https://cdn.example/album/photo-1_sm.jpg",
                "https://cdn.example/album/photo-2_md.webp",
            ]
        )
        self.assertEqual(
            photos,
            [
                "https://cdn.example/album/photo-1_md.webp",
                "https://cdn.example/album/photo-2_md.webp",
            ],
        )

    def test_premier_uses_listing_gallery_items_and_ignores_related_gallery(self):
        soup = BeautifulSoup(
            """
            <div class="gallery">
              <div class="gallery-item"><img data-src="https://cdn.example/home-1.jpg"></div>
              <div class="gallery-item"><img data-src="https://cdn.example/home-2.jpg"></div>
            </div>
            <div class="related gallery">
              <div class="gallery-item"><img data-src="https://cdn.example/other-home.jpg"></div>
            </div>
            <div class="agent-card"><img src="https://cdn.example/agent.jpg"></div>
            """,
            "lxml",
        )

        photos = _extrair_fotos_premier(
            soup,
            "https://www.premiermarilia.com.br/imovel/62794386/venda/casa",
        )

        self.assertEqual(
            photos,
            [
                "https://cdn.example/home-1.jpg",
                "https://cdn.example/home-2.jpg",
            ],
        )

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


class PropertyDescriptionExtractionTests(unittest.TestCase):
    def test_gilmar_description_is_taken_from_the_copy_following_its_heading(self):
        description = (
            "IMÓVEL COM ÓTIMA LOCALIZAÇÃO. POSSUI 3 DORMITÓRIOS COM ARMÁRIOS "
            "SENDO 1 SUÍTE, SALA, COZINHA COM ARMÁRIOS, ÁREA GOURMET E GARAGEM "
            "COM 3 VAGAS."
        )
        soup = BeautifulSoup(
            f"""
            <main>
              <div class="col-12 mb-5">
                <span>Sobre o imóvel</span>
                <div class="text-justify">{description}</div>
              </div>
              <div class="col-12 my-5">
                Especificações Imóvel Construído; Nossa Localização e imóveis relacionados
              </div>
            </main>
            """,
            "lxml",
        )

        extracted = _extrair_descricao(soup, soup.get_text(" ", strip=True))

        self.assertEqual(extracted, description)

    def test_premier_prefers_property_copy_to_condominium_copy(self):
        property_copy = (
            "Casa com quatro dormitórios, suíte, sala ampla, cozinha planejada, "
            "quintal e quatro vagas de garagem em excelente estado."
        )
        soup = BeautifulSoup(
            f"""
            <div class="property-description-text">{property_copy}</div>
            <div class="condo-description">
              Condomínio com piscina, quadra esportiva, salão de festas e portaria.
            </div>
            """,
            "lxml",
        )

        extracted = _extrair_descricao(
            soup,
            soup.get_text(" ", strip=True),
        )

        self.assertEqual(extracted, property_copy)

    def test_missing_listing_copy_does_not_fall_back_to_entire_page_text(self):
        page_copy = (
            "Imobiliária Marília contato atendimento e ofertas. Imóveis relacionados "
            "com quartos, banheiros, área e garagem. Entre em contato agora."
        )
        soup = BeautifulSoup(f"<main><div>{page_copy}</div></main>", "lxml")

        self.assertEqual(_extrair_descricao(soup, page_copy), "")


class DescriptionReformulationTests(unittest.TestCase):
    def test_rejects_materially_shortened_reformulation(self):
        original = "Casa com cozinha planejada, lavanderia, área gourmet e garagem coberta para dois carros."
        shortened = "Casa com ambientes planejados e garagem."

        self.assertFalse(_reformulacao_preserva_descricao(original, shortened))

    def test_accepts_reformulation_that_keeps_similar_content_length(self):
        original = "Casa com cozinha planejada, lavanderia, área gourmet e garagem coberta para dois carros."
        reformulated = "Casa com cozinha planejada e lavanderia, área gourmet completa e garagem coberta para dois veículos."

        self.assertTrue(_reformulacao_preserva_descricao(original, reformulated))
