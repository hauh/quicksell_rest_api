"""Base models and models' common things."""

from django.db.models import Manager, Model


class QuicksellManager(Manager):
	"""Custom Manager."""

	use_in_migrations = True

	def get_or_none(self, **kwargs):
		try:
			return self.get(**kwargs)
		except self.model.DoesNotExist:
			return None


class QuicksellModel(Model):
	"""Model to use with custom Manager."""

	objects = QuicksellManager()

	class Meta:
		abstract = True
