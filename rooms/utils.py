import random
import string

from .models import Room

def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=6))

        if not Room.objects.filter(code=code).exists():
            return code