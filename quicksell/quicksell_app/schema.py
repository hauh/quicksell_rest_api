"""Schema generation with drf_yasg."""

from rest_framework.serializers import ModelSerializer
from drf_yasg.inspectors import SwaggerAutoSchema
from drf_yasg.openapi import Schema, Info, License
from drf_yasg.views import get_schema_view
from drf_yasg.utils import force_serializer_instance


schema_info = Info(
	title="Quicksell API",
	default_version='v1',
	license=License(name="Proprietary"),
)
schema_view = get_schema_view(schema_info, public=True)


class NoRefNameMeta:
	"""Serializers with this Meta won't be defined and referenced."""
	ref_name = None


class FilteringFieldsAutoSchema(SwaggerAutoSchema):
	"""Custom schema generator.
	Excludes non-model serializer from definitions.
	Filters out `read_only` fields in request body and `write_only` in response.
	"""

	implicit_body_methods = ('PUT', 'PATCH', 'POST', 'DELETE')

	def serializer_to_schema(self, serializer):
		if not isinstance(serializer, ModelSerializer):
			if not hasattr(serializer, 'Meta'):
				setattr(serializer, 'Meta', NoRefNameMeta)
			elif not hasattr(serializer.Meta, 'ref_name'):
				setattr(serializer.Meta, 'ref_name', None)
		return super().serializer_to_schema(serializer)

	def get_request_body_schema(self, serializer):
		schema = self.serializer_to_schema(serializer)
		if isinstance(schema, Schema):
			for name, field in serializer.fields.items():
				if field.read_only:
					schema['properties'].pop(name)
		return schema

	def get_response_schemas(self, response_serializers):
		processed_serializers = {}
		for sc, serializer in response_serializers.items():
			try:
				serializer_instance = force_serializer_instance(serializer)
			except AssertionError:
				processed_serializers[sc] = serializer
				continue

			schema = self.serializer_to_schema(serializer_instance)
			if isinstance(schema, Schema):
				for name, field in serializer_instance.fields.items():
					if field.write_only:
						schema['properties'].pop(name)

				if 'required' in schema:
					filtered_required = [
						name for name in schema['required']
						if name in schema['properties']
					]
					if filtered_required:
						schema['required'] = filtered_required
					else:
						schema.pop('required')
			processed_serializers[sc] = schema

		return super().get_response_schemas(processed_serializers)
