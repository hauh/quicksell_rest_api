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


class SerializationMixin:
	"""Manual serialization for tests."""

	def serialize(self):
		# breaking circular import - pylint: disable=import-outside-toplevel
		from quicksell_app import serializers
		try:
			return getattr(serializers, self.__class__.__name__)(self).data
		except AttributeError:
			return str(self)


class QuicksellModel(Model, SerializationMixin):
	"""Model to use with custom Manager."""

	objects = QuicksellManager()

	class Meta:
		abstract = True
