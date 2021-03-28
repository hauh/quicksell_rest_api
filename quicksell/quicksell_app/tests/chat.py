"""Chats tests."""

import uuid
from unittest import mock

from django.urls import reverse
from model_bakery import baker
from rest_framework.status import (
	HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST,
	HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
)

from quicksell_app import models

from .basetest import BaseTest


class BaseChatTest(BaseTest):
	"""Common for endpoints at `api/chats/`."""

	chats_url = reverse('chat')

	def setUp(self):
		self.make_user()
		self.user.device = baker.make('FCMDevice')
		self.interlocutor = baker.make(
			self.user_model, make_m2m=True, device=baker.make('FCMDevice')
		)
		self.interlocutor_uuid = self.base64uuid(self.interlocutor.profile.uuid)
		self.listing = baker.make('Listing', seller=self.interlocutor.profile)
		self.listing_uuid = self.base64uuid(self.listing.uuid)
		self.authorize()


class TestChat(BaseChatTest):
	"""GET, POST api/chats/"""

	def setUp(self):
		super().setUp()
		self.data = {
			'text': "Hello!",
			'to_uuid': self.interlocutor_uuid,
			'listing_uuid': self.listing_uuid
		}

	@mock.patch.object(BaseTest.user_model, 'push_notification')
	def test_create_chat(self, mocked_push):
		# create chat
		response = self.POST(self.chats_url, HTTP_201_CREATED, self.data)
		self.assertEqual(models.Chat.objects.count(), 1)
		self.assertIn('uuid', response.data)
		mocked_push.assert_called_once()
		# check interlocutor
		self.assertIn('interlocutor', response.data)
		interlocutor = response.data['interlocutor']
		self.assertIn('uuid', interlocutor)
		self.assertEqual(interlocutor['uuid'], self.data['to_uuid'])
		# check listing
		self.assertIn('listing', response.data)
		listing = response.data['listing']
		self.assertIn('uuid', listing)
		self.assertEqual(listing['uuid'], self.data['listing_uuid'])
		self.assertIn('subject', response.data)
		self.assertEqual(response.data['subject'], listing['title'])
		# check message
		self.assertEqual(models.Message.objects.count(), 1)
		self.assertIn('latest_message', response.data)
		message = response.data['latest_message']
		self.assertEqual(message['text'], self.data['text'])

	@mock.patch.object(BaseTest.user_model, 'push_notification')
	def test_invalid_create(self, mocked_push):
		for missing_field in self.data:
			invalid_data = {**self.data}
			invalid_data.pop(missing_field)
			self.POST(self.chats_url, HTTP_400_BAD_REQUEST, invalid_data)
		for not_in_db in ('to_uuid', 'listing_uuid'):
			invalid_data = {**self.data}
			invalid_data[not_in_db] = self.base64uuid(uuid.uuid4())
			self.POST(self.chats_url, HTTP_404_NOT_FOUND, invalid_data)
		self.client.credentials()
		self.POST(self.chats_url, HTTP_401_UNAUTHORIZED, self.data)
		mocked_push.assert_not_called()

	def test_get_chats(self):
		self.assertEqual(models.Chat.objects.count(), 0)
		q = 33
		chats = baker.make('Chat', make_m2m=True, _quantity=q, creator=self.user)
		for chat in chats:
			baker.make('Message', chat=chat)
		self.query_paginated_result(self.chats_url, None, q)
		baker.make('Chat', make_m2m=True, _quantity=q, creator=self.interlocutor)
		self.assertEqual(models.Chat.objects.count(), q * 2)
		self.query_paginated_result(self.chats_url, None, q)


@mock.patch.object(BaseTest.user_model, 'push_notification')
class TestMessage(BaseChatTest):
	"""GET, POST api/chats/<base64uuid>/"""

	def setUp(self):
		super().setUp()
		self.chat = baker.make(
			models.Chat, make_m2m=True,
			creator=self.user, interlocutor=self.interlocutor
		)
		self.chat_uuid = self.base64uuid(self.chat.uuid)
		self.messages_url = reverse('message', args=(self.chat_uuid,))

	def test_post_message(self, mocked_push):
		for user in (self.user, self.interlocutor):
			self.authorize(user)
			for text in ("Hello", "How are you?", "Whatever", "Goodbye!"):
				response = self.POST(self.messages_url, HTTP_201_CREATED, {'text': text})
				self.assertIn('text', response.data)
				self.assertEqual(response.data['text'], text)
				self.assertIn('is_yours', response.data)
				self.assertEqual(response.data['is_yours'], True)
				self.assertIn('read', response.data)
				self.assertEqual(response.data['read'], False)
				self.assertIn('timestamp', response.data)
				mocked_push.assert_called_once_with(
					title=user.profile.full_name, body=text
				)
				mocked_push.reset_mock()

	def test_invalid_post(self, mocked_push):
		self.POST(self.messages_url, HTTP_400_BAD_REQUEST, {'text': None})
		self.POST(self.messages_url, HTTP_400_BAD_REQUEST)
		self.client.credentials()
		self.POST(self.messages_url, HTTP_401_UNAUTHORIZED, {'text': "good"})
		mocked_push.assert_not_called()

		third_user = baker.make(self.user_model, make_m2m=True)
		self.authorize(third_user)
		self.POST(self.chats_url, HTTP_201_CREATED, {
			'text': 'good',
			'to_uuid': self.interlocutor_uuid,
			'listing_uuid': self.listing_uuid
		})
		mocked_push.assert_called_once()
		self.POST(self.messages_url, HTTP_403_FORBIDDEN, {'text': 'good'})
		mocked_push.assert_called_once()

	def test_load_chat(self, mocked_push):
		q = 123
		strings = [uuid.uuid4().hex for _ in range(q)]
		for message in strings:
			self.POST(self.messages_url, HTTP_201_CREATED, {'text': message})
		self.assertEqual(mocked_push.call_count, q)

		for user, is_yours, read_status in (
			(self.user, True, False),
			(self.interlocutor, False, False),
			(self.interlocutor, False, True),
		):
			self.authorize(user)
			first_page, _ = self.query_paginated_result(self.messages_url, None, q)
			self.assertIn('results', first_page.data)
			for sent, saved in zip(first_page.data['results'], reversed(strings)):
				self.assertDictContainsSubset(
					{'text': saved, 'is_yours': is_yours, 'read': read_status}, sent
				)

		self.authorize(self.interlocutor)
		for message in strings:
			self.POST(self.messages_url, HTTP_201_CREATED, {'text': message})
		self.query_paginated_result(self.messages_url, None, q * 2)
		self.assertEqual(mocked_push.call_count, q * 2)

	def test_invalid_load(self, _mocked_push):
		msg_count = 10
		for author in (self.user, self.interlocutor):
			baker.make('Message', _quantity=msg_count, chat=self.chat, author=author)
		self.assertEqual(models.Message.objects.count(), msg_count * 2)
		self.query_paginated_result(self.messages_url, None, msg_count * 2)
		self.GET(self.messages_url[:-2] + '/', HTTP_404_NOT_FOUND)
		third_user = baker.make(self.user_model, make_m2m=True)
		self.authorize(third_user)
		self.GET(self.messages_url, HTTP_403_FORBIDDEN)

	def test_delete_chat(self, _mocked_push):
		self.assertEqual(models.Chat.objects.count(), 1)
		self.DELETE(self.messages_url, HTTP_204_NO_CONTENT)
		self.assertEqual(models.Chat.objects.count(), 0)
