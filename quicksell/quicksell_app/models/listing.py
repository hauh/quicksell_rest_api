"""Listing model."""

from django.db import models
from django.utils import timezone


def default_expiration_date():
	return timezone.now() + timezone.timedelta(days=30)


class Listing(models.Model):
	"""Listing model."""

	class Status(models.IntegerChoices):
		"""Listing's poissble states."""

		draft = 0, 'Draft'
		active = 1, 'Active'
		sold = 2, 'Sold'
		closed = 3, 'Closed'
		deleted = 4, 'Deleted'

	class Category(models.IntegerChoices):
		"""Listing's categories."""

		transport = 1, 'Transport'
		furnishings = 2, 'For houses and dachas'
		belongings = 3, 'Personal belongings'
		hobby = 4, 'Hobby'
		animals = 5, 'Animals'
		electronics = 6, 'Electronics'
		services = 7, 'Sevrvices'

	title = models.CharField(max_length=200)
	description = models.TextField(null=True, blank=True)
	price = models.PositiveIntegerField()
	category = models.PositiveSmallIntegerField(choices=Category.choices)
	status = models.PositiveSmallIntegerField(choices=Status.choices, default=0)
	quantity = models.PositiveIntegerField(default=1)
	sold = models.PositiveIntegerField(default=0)
	views = models.PositiveIntegerField(default=0)
	date_created = models.DateTimeField(default=timezone.now, editable=False)
	date_expires = models.DateTimeField(default=default_expiration_date)
	location = models.ForeignKey(
		'Location', related_name='+', null=True, on_delete=models.SET_NULL)
	seller = models.ForeignKey(
		'Profile', related_name='listings', on_delete=models.CASCADE)
	shop = models.CharField(max_length=100, default='Shop Name')
	# shop = models.ForeignKey(
	# 	'Shop', related_name='listings', on_delete=models.CASCADE)

	def __str__(self):
		return self.title


class Photo(models.Model):
	"""Listing's Photo model."""

	listing = models.ForeignKey(
		'Listing', related_name='photos', on_delete=models.CASCADE)
	image = models.ImageField(upload_to='images/listings/')  # TODO: resize
	order = models.SmallIntegerField(default=0)
