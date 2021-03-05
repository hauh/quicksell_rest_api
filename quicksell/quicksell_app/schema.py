"""Schema generation with drf_yasg."""

from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.openapi import Info, License
from drf_yasg.views import get_schema_view
from drf_yasg.utils import no_body


schema_info = Info(
	title="Quicksell API",
	default_version='v1',
	license=License(name="Proprietary"),
)
schema_view = get_schema_view(schema_info, public=True)


class Read():
	"""Serializer without write_only fields."""

	def get_fields(self):
		return {
			field_name: field
			for field_name, field in super().get_fields().items()
			if not field.write_only
		}


class Write():
	"""Serializer without read_only fields."""

	def get_fields(self):
		return {
			field_name: field
			for field_name, field in super().get_fields().items()
			if not field.read_only
		}


class BlankMeta:
	"""For serializers without Meta."""


class FilteringFieldsAutoSchema(SwaggerAutoSchema):
	"""Splitting serializer into read and write serializers."""

	def convert_serializer(self, new_class):
		serializer = super().get_view_serializer()
		if not serializer:
			return serializer

		class SeparatedFieldsSerializer(new_class, serializer.__class__):
			"""Generated serializer."""
			class Meta(getattr(serializer.__class__, 'Meta', BlankMeta)):
				ref_name = f"{serializer.__class__.__name__} {new_class.__name__}"

		return SeparatedFieldsSerializer(data=serializer.data)

	def get_view_serializer(self):
		return self.convert_serializer(Write)

	def get_default_response_serializer(self):
		body_override = self._get_request_body_override()
		if body_override and body_override is not no_body:
			return body_override
		return self.convert_serializer(Read)
