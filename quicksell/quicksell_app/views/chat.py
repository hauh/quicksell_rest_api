"""Chats and Messages views."""

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
	GenericAPIView, ListCreateAPIView, get_object_or_404
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from quicksell_app import models, serializers


@method_decorator(
	name='get',
	decorator=swagger_auto_schema(
		operation_id='chat-list',
		operation_summary="List of User's Chats",
		operation_description=(
			"Get paginated list of authenticated User's Chats "
			"ordered by `timestamp` of `latest_message`. "
			"`interlocutor` is a Profile of another User in the Chat."
		)
	)
)
@method_decorator(
	name='post',
	decorator=swagger_auto_schema(
		operation_id='chat-create',
		operation_summary="Create Chat",
		operation_description=(
			"Create new Chat with `to_uuid` User and post `text` to it "
			"as a first Message. Chat's `subject` will be set the same as "
			"as a title of Listing from `listing_uuid`."
		)
	)
)
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

	@swagger_auto_schema(
		operation_id='message-list',
		operation_summary="List Messages in Chat",
		operation_description=(
			"Returns paginated list of Messages in Chat (new first).\n"
			"`is_yours` flag indicates author of the Message. "
			"`read` flag indicates whether the Message were read by interlocutor.\n"
			"If `read` == False and `is_yours` == False, "
			"the message is updated with `read` = True as it was read."
		)
	)
	def get(self, request, base64uuid):
		queryset = self.get_chat(request, base64uuid).messages.order_by('-timestamp')
		pages = self.paginate_queryset(queryset)
		serializer = self.get_serializer(pages, many=True)
		response = self.get_paginated_response(serializer.data)
		queryset.exclude(author=request.user).update(read=True)
		return response

	@swagger_auto_schema(
		operation_id='message-create',
		operation_summary="Post Messages to Chat",
		operation_description="Post text as a Message to Chat."
	)
	def post(self, request, base64uuid):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		chat = self.get_chat(request, base64uuid)
		serializer.save(chat=chat, author=request.user)
		return Response(serializer.data, status=HTTP_201_CREATED)
