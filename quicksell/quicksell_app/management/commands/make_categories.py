"""Command to fill Categories from JSON."""

import json
from json.decoder import JSONDecodeError

from django.core.management.base import BaseCommand, CommandError

from quicksell_app.models import Category


def create_category(categories, parent=None):
	for name, branch in categories.items():
		create_category(branch, Category.objects.create(name=name, parent=parent))


class Command(BaseCommand):
	"""Populates Categories table from provided JSON file."""
	help = __doc__

	def add_arguments(self, parser):
		parser.add_argument('filename', type=str)

	def handle(self, *args, filename, **kwargs):
		Category.objects.all().delete()
		try:
			with open(filename, encoding='utf-8') as f:
				create_category(json.load(f))
		except OSError as err:
			raise CommandError("OSError - " + err.args[1]) from err
		except JSONDecodeError as err:
			raise CommandError("JSONDecodeError - " + err.args[0]) from err
		Category.objects.rebuild()
		self.stdout.write(self.style.SUCCESS("Categories updated!"))
