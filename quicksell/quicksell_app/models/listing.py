"""Listing model."""

import uuid
from datetime import datetime, timedelta

from django.db.models import (
	CASCADE, SET, SET_NULL, BooleanField, CharField, DateTimeField, ForeignKey,
	ImageField, IntegerChoices, JSONField, PositiveIntegerField,
	PositiveSmallIntegerField, SmallIntegerField, TextField, UUIDField
)
from mptt.models import MPTTModel, TreeForeignKey

from .basemodel import QuicksellModel


class Category(MPTTModel):
	"""Listing's categories."""

	name = CharField(max_length=64, unique=True)
	parent = TreeForeignKey(
		'self', related_name='children',
		null=True, blank=True, on_delete=CASCADE
	)

	class Meta:
		verbose_name_plural = 'categories'

	class MPTTMeta:  # pylint: disable=missing-class-docstring
		order_insertion_by = ['name']

	def __str__(self):
		return self.name


def uncategorized():
	return Category.objects.get_or_create(name='__uncategorized__')[0].id


def default_expiration_date():
	return datetime.now() + timedelta(days=30)


class Listing(QuicksellModel):
	"""Listing model."""

	class Status(IntegerChoices):
		"""Listing's poissble states."""

		draft = 0, 'Draft'
		active = 1, 'Active'
		sold = 2, 'Sold'
		closed = 3, 'Closed'
		deleted = 4, 'Deleted'

	uuid = UUIDField(default=uuid.uuid4, unique=True, editable=False)
	title = CharField(max_length=200)
	description = TextField(null=True, blank=True)
	price = PositiveIntegerField()
	category = ForeignKey('Category', on_delete=SET(uncategorized))
	status = PositiveSmallIntegerField(choices=Status.choices, default=0)
	quantity = PositiveIntegerField(default=1)
	sold = PositiveIntegerField(default=0)
	views = PositiveIntegerField(default=0)
	date_created = DateTimeField(default=datetime.now, editable=False)
	date_expires = DateTimeField(default=default_expiration_date)
	condition_new = BooleanField(default=False)
	characteristics = JSONField(null=True, blank=True)
	location = ForeignKey(
		'Location', related_name='+', null=True, on_delete=SET_NULL)
	seller = ForeignKey('Profile', related_name='listings', on_delete=CASCADE)

	def __str__(self):
		return self.title


class Photo(QuicksellModel):
	"""Listing's Photo model."""

	listing = ForeignKey('Listing', related_name='photos', on_delete=CASCADE)
	image = ImageField(upload_to='images/listings/')
	order = SmallIntegerField(default=0)
