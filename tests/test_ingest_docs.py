from pathlib import Path
import unittest

from scripts import ingest_docs


FIXTURES = Path(__file__).parent / "fixtures" / "ingest_docs"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class IngestDocsFixturesTest(unittest.TestCase):
    def test_mdn_markdown_frontmatter_macros_and_images(self):
        title, page = ingest_docs.normalize_markdown_page(fixture("mdn.md"), "fallback")
        self.assertEqual(title, "Node")
        self.assertIn("The Node interface is a base class for DOM objects.", page)
        self.assertIn("### Related concepts", page)
        self.assertNotIn("Compat", page)
        self.assertNotIn("decorative diagram", page)

    def test_webdev_markdown_frontmatter_and_template_macros(self):
        title, page = ingest_docs.normalize_markdown_page(fixture("web-dev.md"), "fallback")
        self.assertEqual(title, "Interaction to Next Paint")
        self.assertIn("INP measures interaction responsiveness.", page)
        self.assertIn("### Thresholds", page)
        self.assertNotIn("{% Img", page)

    def test_whatwg_source_filters_navigation_and_nonstandard_variant(self):
        source = fixture("whatwg-source.html")
        parser = ingest_docs.HTMLToMarkdown(source, whatwg=True)
        parser.feed(source)
        text = parser.markdown()
        self.assertIn("The dialog element", text)
        self.assertIn("makes the rest of the document inert", text)
        self.assertNotIn("Table of contents noise", text)
        self.assertNotIn("web developer edition", text)
        self.assertNotIn("editor-only table fragment", text)

    def test_apg_html_strips_navigation_and_code_samples(self):
        title, page = ingest_docs.normalize_html_page(fixture("apg.html"), "fallback")
        self.assertEqual(title, "Dialog (Modal) Pattern")
        self.assertIn("Escape closes the dialog", page)
        self.assertNotIn("Site navigation noise", page)
        self.assertNotIn("long implementation sample", page)

    def test_wcag_html_preserves_preformatted_document_text(self):
        title, page = ingest_docs.normalize_html_page(
            fixture("wcag.html"), "fallback", preserve_pre=True
        )
        self.assertEqual(title, "Web Content Accessibility Guidelines 2.2")
        self.assertIn("### Target Size (Minimum)", page)
        self.assertIn("Normative example text stays verbatim.", page)
        self.assertNotIn("techniques.html", page)

    def test_react_mdx_removes_presentation_wrappers(self):
        title, page = ingest_docs.normalize_markdown_page(fixture("react.mdx"), "fallback")
        self.assertEqual(title, "You Might Not Need an Effect")
        self.assertIn("Effects are an escape hatch", page)
        self.assertIn("### You might not need an Effect", page)
        self.assertNotIn("<Intro>", page)

    def test_angular_generated_markdown_drops_nav_and_shifts_page_heading(self):
        text = ingest_docs.clean_markdown(fixture("angular.txt"))
        text = ingest_docs.shift_headings(text, 1)
        self.assertIn("## Angular coding style guide", text)
        self.assertIn("### Components", text)
        self.assertIn("Prefer focused components.", text)
        self.assertNotIn("Navigation boilerplate", text)
        self.assertNotIn(".navigation { display: none; }", text)
        self.assertIn("`{{value}}`", text)
        self.assertIn("import LiteYouTube from './LiteYouTube';", text)
        self.assertIn('<nav aria-label="example">Example markup stays.</nav>', text)

    def test_playwright_markdown_removes_import_and_admonition_wrappers(self):
        title, page = ingest_docs.normalize_markdown_page(fixture("playwright.md"), "fallback")
        self.assertEqual(title, "Clock")
        self.assertIn("Install the clock before using timers.", page)
        self.assertIn("### Introduction", page)
        self.assertNotIn("import LiteYouTube", page)
        self.assertNotIn(":::note", page)


if __name__ == "__main__":
    unittest.main()
