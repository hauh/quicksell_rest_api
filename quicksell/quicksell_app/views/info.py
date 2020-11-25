"""Info about API settings."""

from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from quicksell_app.models import Category as category_model


def build_tree(categories, parent):
	subtree = {}
	for category in categories:
		if category['parent'] == parent:
			subtree[category['name']] = build_tree(categories, category['id'])
	return subtree


class Info(GenericAPIView):
	"""Categories tree."""

	queryset = category_model.objects.exclude(name='__uncategorized__')
	pagination_class = None

	@swagger_auto_schema(
		operation_id='info',
		operation_summary='API Info',
		operation_description="Returns Categories tree.",
		security=[],
		responses={HTTP_200_OK: "Nested JSON with Categories."}
	)
	def get(self, _request):
		categories = self.get_queryset().values('id', 'parent', 'name')
		tree = build_tree(categories, None)
		return Response({'categories': tree}, HTTP_200_OK)
