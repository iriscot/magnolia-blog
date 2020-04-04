import json
from collections import namedtuple
from yattag import Doc


class RichFormatter(object):
	"""docstring for RichFormatter"""
	def __init__(self, jsonData):
		super(RichFormatter, self).__init__()
		self.jsonData = jsonData

	def toHTML(self):
		structure = json.loads(self.jsonData, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

		doc, tag, text, line = Doc().ttl()

		for block in structure.blocks:
			if block.type == 'header':
				line('h'+str(block.data.level), block.data.text)

			if block.type == 'paragraph':
				with tag('p', klass='post-entry'):
					doc.asis(block.data.text)

			if block.type == 'image':
				with tag('figure', klass='post-entry post-picture '+('full-width' if block.data.stretched else '')):
					doc.stag('img', src=block.data.file.url, alt=block.data.caption)
					with tag('figcaption'):
						text(block.data.caption)

			if block.type == 'raw':
				doc.asis(block.data.html)

			if block.type == 'list':
				with tag('ul' if block.data.style == 'unordered' else 'ol'):
					for item in block.data.items:
						line('li', item)

			if block.type == 'quote':
				with tag('blockquote', klass='post-entry post-quote'+ ' centered' if block.data.alignment == 'center' else ''):
					with tag('p'):
						doc.asis(block.data.text)
					with tag('footer'):
						text(block.data.caption)


			if block.type == 'embed':
				if block.data.service == 'youtube':
					with tag('figure', klass='post-entry post-vide full-width'):
						line('iframe', '', width='100%', height='600px', src=block.data.embed, frameborder=0, allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture', allowfullscreen='allowfullscreen')
						with tag('figcaption'):
							text(block.data.caption)
			

			if block.type == 'checklist':
				with tag('ul', klass='post-entry checklist'):
					for item in block.data.items:
						line('li', item.text, klass='checked' if item.checked else '')


			if block.type == 'delimiter':
				line('div', '', klass='delimiter')


		return doc.getvalue()

