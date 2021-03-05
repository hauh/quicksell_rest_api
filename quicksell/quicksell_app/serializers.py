"""User serilaizers."""

from uuid import UUID

from django.contrib.auth import password_validation
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.fields import CharField, Field, IntegerField
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from quicksell_app import models


class Base64UUIDField(Field):
	"""UUID to pretty base64 format."""

	def to_representation(self, value):
		return urlsafe_base64_encode(value.bytes)

	def to_internal_value(self, data):
		if isinstance(data, UUID):
			return data
		try:
			return UUID(bytes=urlsafe_base64_decode(data))
		except ValueError as err:
			raise NotFound() from err


class Profile(ModelSerializer):
	"""Users' Profile info."""

	uuid = Base64UUIDField(read_only=True)

	class Meta:
		model = models.Profile
		fields = (
			'uuid', 'date_created', 'full_name', 'about',
			'online', 'rating', 'avatar', 'location'
		)
		read_only_fields = ('uuid', 'date_created', 'online', 'rating', 'location')


class User(ModelSerializer):
	"""Users's account."""

	profile = Profile(read_only=True)

	class Meta:
		model = models.User
		fields = (
			'email', 'password', 'is_email_verified',
			'date_joined', 'balance', 'profile'
		)
		read_only_fields = ('is_email_verified', 'date_joined', 'balance', 'profile')
		extra_kwargs = {'password': {'write_only': True}}

	def validate_password(self, password):
		password_validation.validate_password(password)
		return password

	def create(self, validated_data):
		return self.Meta.model.objects.create_user(**validated_data)


class CategoryField(Field):
	"""Listing's category."""

	def to_representation(self, category):
		return category.name

	def to_internal_value(self, category_name):
		try:
			category = models.Category.objects.get(name=category_name)
		except models.Category.DoesNotExist as err:
			raise ValidationError("Category doesn't exist.") from err
		if not category.is_leaf_node():
			raise ValidationError("Category should be at lowest level.")
		return category


class Listing(ModelSerializer):
	"""Listing info."""

	uuid = Base64UUIDField(read_only=True)
	price = IntegerField(min_value=0)
	seller = Profile(read_only=True)
	category = CategoryField()

	class Meta:
		model = models.Listing
		fields = (
			'uuid', 'title', 'description', 'price', 'category', 'status',
			'quantity', 'sold', 'views', 'date_created', 'date_expires',
			'location', 'condition_new', 'characteristics', 'seller', 'photos'
		)
		depth = 1
		read_only_fields = (
			'uuid', 'sold', 'views', 'date_created',
			'date_expires', 'seller', 'shop', 'photos'
		)
		ordering = 'created'


class Message(ModelSerializer):
	"""Chat's message serializer."""

	yours = SerializerMethodField()

	class Meta:
		model = models.Message
		fields = 'yours', 'text', 'date_sent', 'read'
		read_only_fields = fields

	def get_yours(self, message_object):
		return self.context['request'].user == message_object.author


class Chat(ModelSerializer):
	"""Chat serializer."""

	# POST
	text = CharField(write_only=True)
	to_uuid = Base64UUIDField(write_only=True)
	listing_uuid = Base64UUIDField(write_only=True)

	# GET
	uuid = Base64UUIDField(read_only=True)
	interlocutor = SerializerMethodField()
	listing = Listing(read_only=True)
	latest_message = SerializerMethodField()

	class Meta:
		model = models.Chat
		fields = (
			'to_uuid', 'listing_uuid', 'text',
			'uuid', 'subject', 'interlocutor', 'listing', 'latest_message'
		)
		read_only_fields = fields

	def get_interlocutor(self, chat_object):
		if self.context['request'].user != chat_object.creator:
			interlocutor_profile = chat_object.creator.profile
		else:
			interlocutor_profile = chat_object.interlocutor.profile
		return Profile(interlocutor_profile, context=self.context).data

	def get_latest_message(self, chat_object):
		latest_message = chat_object.messages.latest('date_sent')
		return Message(latest_message, context=self.context).data

	def create(self, val_data):
		creator = self.context['request'].user
		to_user = get_object_or_404(models.Profile, uuid=val_data['to_uuid']).user
		listing = get_object_or_404(models.Listing, uuid=val_data['listing_uuid'])
		with transaction.atomic():
			new_chat = models.Chat.objects.create(
				creator=creator,
				interlocutor=to_user,
				listing=listing,
				subject=listing.title
			)
			models.Message.objects.create(
				text=val_data['text'], author=creator, chat=new_chat
			)
		return new_chat
