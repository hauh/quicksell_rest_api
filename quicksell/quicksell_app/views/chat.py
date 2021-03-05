"""Chats and Messages views."""

from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated

from quicksell_app import models, serializers


class Chat(ListCreateAPIView):
	"""List User's Chats or create new."""

	serializer_class = serializers.Chat
	permission_classes = (IsAuthenticated,)

	def get_queryset(self):
		return (
			models.Chat.objects.filter(creator=self.request.user)
			| models.Chat.objects.filter(interlocutor=self.request.user)
		).order_by('updated_at')
