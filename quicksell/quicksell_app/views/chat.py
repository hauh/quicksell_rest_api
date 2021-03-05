"""Chats and Messages views."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
	GenericAPIView, ListCreateAPIView, get_object_or_404
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

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


class Message(GenericAPIView):
	"""List Messages from a Chat or post to one."""

	serializer_class = serializers.Message
	permission_classes = (IsAuthenticated,)

	def get_chat(self, request, base64uuid):
		uuid = serializers.Base64UUIDField().to_internal_value(base64uuid)
		chat_object = get_object_or_404(models.Chat.objects.filter(uuid=uuid))
		if request.user not in (chat_object.creator, chat_object.interlocutor):
			raise PermissionDenied()
		return chat_object

	def get(self, request, base64uuid):
		queryset = self.get_chat(request, base64uuid).messages.order_by('-timestamp')
		pages = self.paginate_queryset(queryset)
		serializer = self.get_serializer(pages, many=True)
		response = self.get_paginated_response(serializer.data)
		queryset.exclude(author=request.user).update(read=True)
		return response

	def post(self, request, base64uuid):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		chat = self.get_chat(request, base64uuid)
		serializer.save(chat=chat, author=request.user)
		return Response(serializer.data, status=HTTP_201_CREATED)
