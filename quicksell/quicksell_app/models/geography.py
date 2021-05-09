"""Geography-related models."""

from django.contrib.gis.db.models.fields import PointField
from django.contrib.gis.geos import Point
from django.db.models.deletion import SET_DEFAULT
from django.db.models.fields import TextField

from .basemodel import QuicksellModel


class Location(QuicksellModel):
	"""Object's physical location."""

	coordinates = PointField(unique=True)
	address = TextField(max_length=1024)

	@classmethod
	def default_pk(cls):
		return cls.objects.get_or_create(
			coordinates=Point(x=55.751426, y=37.618879),
			address="The Kremlin"
		)[0].id


location_fk_kwargs = {
	'to': Location,
	'related_name': '+',
	'on_delete': SET_DEFAULT,
	'default': Location.default_pk,
}
