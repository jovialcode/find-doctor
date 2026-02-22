"""Tests for parser module."""

import pytest

from collector.parser.base import FieldRule, ParserRule
from collector.parser.selector_parser import SelectorParser


class TestSelectorParser:
    """Tests for SelectorParser."""

    @pytest.fixture
    def parser(self) -> SelectorParser:
        """Create parser instance."""
        return SelectorParser()

    @pytest.fixture
    def sample_html(self) -> str:
        """Sample HTML for testing."""
        return """
        <html>
        <body>
            <div class="doctor-list">
                <div class="doctor-item">
                    <h3 class="name">김철수</h3>
                    <span class="specialty">내과</span>
                    <a class="profile" href="/doctor/001">프로필</a>
                </div>
                <div class="doctor-item">
                    <h3 class="name">박영희</h3>
                    <span class="specialty">외과</span>
                    <a class="profile" href="/doctor/002">프로필</a>
                </div>
            </div>
        </body>
        </html>
        """

    def test_parse_list(self, parser: SelectorParser, sample_html: str) -> None:
        """Test parsing a list of items."""
        rule = ParserRule(
            name="doctor_list",
            container="div.doctor-list",
            item="div.doctor-item",
            fields=[
                FieldRule(name="name", selector="h3.name", type="text"),
                FieldRule(name="specialty", selector="span.specialty", type="text"),
                FieldRule(
                    name="profile_url",
                    selector="a.profile",
                    type="url",
                    attribute="href",
                ),
            ],
        )

        result = parser.parse(sample_html, rule, source_url="https://example.com")

        assert result.is_success
        assert result.item_count == 2

        assert result.data[0]["name"] == "김철수"
        assert result.data[0]["specialty"] == "내과"
        assert result.data[0]["profile_url"] == "https://example.com/doctor/001"

        assert result.data[1]["name"] == "박영희"
        assert result.data[1]["specialty"] == "외과"

    def test_parse_single(self, parser: SelectorParser) -> None:
        """Test parsing a single item."""
        html = """
        <div class="doctor-detail">
            <h1 class="name">김철수 교수</h1>
            <img class="photo" src="/images/doc001.jpg" />
            <ul class="education">
                <li>서울대학교 의과대학</li>
                <li>서울대학교병원 전공의</li>
            </ul>
        </div>
        """

        fields = [
            FieldRule(name="name", selector="h1.name", type="text"),
            FieldRule(
                name="photo_url",
                selector="img.photo",
                type="url",
                attribute="src",
            ),
            FieldRule(
                name="education",
                selector="ul.education li",
                type="text_list",
            ),
        ]

        result = parser.parse_single(html, fields, source_url="https://hospital.com")

        assert result.is_success
        assert result.item_count == 1
        assert result.data[0]["name"] == "김철수 교수"
        assert result.data[0]["photo_url"] == "https://hospital.com/images/doc001.jpg"
        assert result.data[0]["education"] == [
            "서울대학교 의과대학",
            "서울대학교병원 전공의",
        ]

    def test_transform_strip(self, parser: SelectorParser) -> None:
        """Test strip transform."""
        html = "<div class='name'>  김철수  </div>"

        fields = [
            FieldRule(
                name="name",
                selector="div.name",
                type="text",
                transform=[{"type": "strip"}],
            ),
        ]

        result = parser.parse_single(html, fields)
        assert result.data[0]["name"] == "김철수"

    def test_transform_regex_extract(self, parser: SelectorParser) -> None:
        """Test regex extract transform."""
        html = "<div class='name'>김철수 교수</div>"

        fields = [
            FieldRule(
                name="name",
                selector="div.name",
                type="text",
                transform=[
                    {"type": "regex_extract", "pattern": r"^(.+?)\s+교수$", "group": 1}
                ],
            ),
        ]

        result = parser.parse_single(html, fields)
        assert result.data[0]["name"] == "김철수"

    def test_missing_selector_returns_default(self, parser: SelectorParser) -> None:
        """Test that missing selectors return default values."""
        html = "<div class='other'>content</div>"

        fields = [
            FieldRule(
                name="name",
                selector="div.name",
                type="text",
                default="Unknown",
            ),
        ]

        result = parser.parse_single(html, fields)
        assert result.data[0]["name"] == "Unknown"

    def test_container_not_found(self, parser: SelectorParser) -> None:
        """Test handling when container is not found."""
        html = "<div class='other'>content</div>"

        rule = ParserRule(
            name="test",
            container="div.missing-container",
            item="div.item",
            fields=[FieldRule(name="name", selector=".name", type="text")],
        )

        result = parser.parse(html, rule)

        assert not result.is_success
        assert len(result.errors) > 0
