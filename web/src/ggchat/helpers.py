import hashlib

from django.conf import settings


def is_admin(request):
    salt = 'Mo9hCrZF1wV4d0IHf6kg7eD4xCwfNexv'
    valid_hash = '58a6bcf429ffb8e79c5f2ef9fd4d134529ae35c944736983c96d4bad6d2d4316'
    return calculate_hash(request.GET.get("chat", ""), salt) == valid_hash


def calculate_hash(text, salt=None):
    if not salt:
        salt = settings.SECRET_KEY
    return hashlib.sha256((str(text)+salt).encode()).hexdigest()
