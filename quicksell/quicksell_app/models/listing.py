"""Listing model."""

import uuid

from django.db import models


class Listing(models.Model):
	"""Listing model."""

	class Category(models.TextChoices):
		"""Listing's categories."""

		CAT1 = '1', 'Category1'
		CAT2 = '2', 'Category2'
		CAT3 = '3', 'Category3'
		CAT4 = '4', 'Category4'

	listing_id = models.UUIDField(unique=True, default=uuid.uuid4)
	title = models.CharField(max_length=200)
	sold = models.BooleanField(default=False)
	closed = models.BooleanField(default=False)
	category = models.CharField(max_length=2, choices=Category.choices)
	location = models.ForeignKey('Location', null=True, on_delete=models.SET_NULL)
	photo_filename = models.CharField(max_length=20, null=True)
	date_created = models.DateTimeField(auto_now_add=True)
	owner = models.ForeignKey(
		'User', on_delete=models.CASCADE, related_name='listings')
