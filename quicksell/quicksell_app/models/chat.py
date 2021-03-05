"""Chat and Message models."""

import uuid

from django.db.models import (
	CASCADE, BooleanField, CharField, DateTimeField, ForeignKey, TextField,
	UUIDField
)

from .basemodel import QuicksellModel


class Chat(QuicksellModel):
	"""User's chat."""

	uuid = UUIDField(default=uuid.uuid4, unique=True, editable=False)
	creator = ForeignKey(
		'User', related_name='created_chats', on_delete=CASCADE, editable=False
	)
	interlocutor = ForeignKey(
		'User', related_name='participated_chats', on_delete=CASCADE, editable=False
	)
	listing = ForeignKey(
		'Listing', related_name='chats', on_delete=CASCADE,
		editable=False, null=True
	)
	subject = CharField(max_length=200)
	updated_at = DateTimeField(auto_now=True)


class Message(QuicksellModel):
	"""Message in Chat."""

	chat = ForeignKey(
		Chat, related_name='messages', on_delete=CASCADE, editable=False
	)
	author = ForeignKey(
		'User', related_name='+', on_delete=CASCADE, editable=False
	)
	text = TextField(max_length=2000)
	date_sent = DateTimeField(auto_now_add=True)
	read = BooleanField(default=False)
