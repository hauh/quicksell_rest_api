"""Permissions."""

from rest_framework import permissions


class AccessProfile(permissions.BasePermission):
	"""Restricts control over account to it's owner or stuff."""

	def has_object_permission(self, request, view, obj):
		return request.user.is_staff or obj == request.user
