import json
from html import escape
from urllib.parse import urlparse

import bleach
from yattag import Doc


ALLOWED_INLINE_TAGS = [
    'a', 'abbr', 'b', 'br', 'code', 'em', 'i', 'mark', 's', 'span', 'strong', 'sub', 'sup', 'u'
]
ALLOWED_BLOCK_TAGS = ALLOWED_INLINE_TAGS + [
    'blockquote', 'div', 'figcaption', 'figure', 'h2', 'h3', 'hr', 'li', 'ol', 'p', 'pre', 'ul'
]
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'a': ['href', 'rel', 'target', 'title'],
    'span': ['class'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


class RichFormatter:
    def __init__(self, json_data):
        self.json_data = json_data or '{}'

    def toHTML(self):  # noqa: N802 - keep the public API used by models.py
        try:
            structure = json.loads(self.json_data)
        except (TypeError, ValueError):
            return ''

        doc, tag, text, line = Doc().ttl()
        for block in structure.get('blocks', []):
            block_type = block.get('type')
            data = block.get('data') or {}

            if block_type == 'header':
                level = data.get('level', 2)
                if level not in {2, 3, 4, 5, 6}:
                    level = 2
                line(f'h{level}', data.get('text', ''))

            elif block_type == 'paragraph':
                with tag('p', klass='post-entry'):
                    doc.asis(self._clean_inline(data.get('text', '')))

            elif block_type == 'image':
                image_url = self._safe_media_url((data.get('file') or {}).get('url', ''))
                if image_url:
                    css_class = 'post-entry post-picture'
                    if data.get('stretched'):
                        css_class += ' full-width'
                    with tag('figure', klass=css_class):
                        caption = data.get('caption', '')
                        doc.stag('img', src=image_url, alt=escape(caption))
                        with tag('figcaption'):
                            text(caption)

            elif block_type == 'raw':
                doc.asis(self._clean_block(data.get('html', '')))

            elif block_type == 'list':
                list_style = data.get('style', 'unordered')
                tag_name = 'ol' if list_style == 'ordered' else 'ul'
                css_class = 'post-entry checklist' if list_style == 'checklist' else 'post-entry'
                with tag(tag_name, klass=css_class):
                    self._render_list_items(doc, tag, data.get('items', []), list_style)

            elif block_type == 'quote':
                css_class = 'post-entry post-quote'
                if data.get('alignment') == 'center':
                    css_class += ' centered'
                with tag('blockquote', klass=css_class):
                    with tag('p'):
                        doc.asis(self._clean_inline(data.get('text', '')))
                    with tag('footer'):
                        text(data.get('caption', ''))

            elif block_type == 'embed' and data.get('service') == 'youtube':
                embed_url = self._safe_youtube_embed(data.get('embed', ''))
                if embed_url:
                    with tag('figure', klass='post-entry post-vide full-width'):
                        line(
                            'iframe', '', width='100%', height='600', src=embed_url,
                            frameborder='0',
                            allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture',
                            allowfullscreen='allowfullscreen',
                        )
                        with tag('figcaption'):
                            text(data.get('caption', ''))

            elif block_type == 'checklist':
                with tag('ul', klass='post-entry checklist'):
                    self._render_list_items(doc, tag, data.get('items', []), 'checklist')

            elif block_type == 'delimiter':
                line('div', '', klass='delimiter')

        return doc.getvalue()


    def _render_list_items(self, doc, tag, items, list_style):
        is_checklist = list_style == 'checklist'
        nested_tag = 'ol' if list_style == 'ordered' else 'ul'

        for item in items:
            item_text, nested_items, checked = self._extract_list_item(item)

            if is_checklist:
                with tag('li', klass='checked' if checked else ''):
                    doc.asis(self._clean_inline(item_text))
                    if nested_items:
                        with tag('ul', klass='checklist'):
                            self._render_list_items(doc, tag, nested_items, list_style)
            else:
                with tag('li'):
                    doc.asis(self._clean_inline(item_text))
                    if nested_items:
                        with tag(nested_tag):
                            self._render_list_items(doc, tag, nested_items, list_style)

    @staticmethod
    def _extract_list_item(item):
        if not isinstance(item, dict):
            return item, [], False

        meta = item.get('meta') or {}
        checked = bool(meta.get('checked', item.get('checked', False)))
        text = item.get('content', item.get('text', ''))
        return text, item.get('items', []), checked

    @staticmethod
    def _clean_inline(value):
        return bleach.clean(
            str(value or ''),
            tags=ALLOWED_INLINE_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )

    @staticmethod
    def _clean_block(value):
        return bleach.clean(
            str(value or ''),
            tags=ALLOWED_BLOCK_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )

    @staticmethod
    def _safe_media_url(value):
        value = str(value or '')
        parsed = urlparse(value)
        if parsed.scheme or parsed.netloc:
            return ''
        if not parsed.path.startswith('/media/'):
            return ''
        return value

    @staticmethod
    def _safe_youtube_embed(value):
        value = str(value or '')
        parsed = urlparse(value)
        if parsed.scheme != 'https':
            return ''
        if parsed.netloc not in {'www.youtube.com', 'youtube.com', 'www.youtube-nocookie.com'}:
            return ''
        if not parsed.path.startswith('/embed/'):
            return ''
        return value
