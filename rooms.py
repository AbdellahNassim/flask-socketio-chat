import random
from string import ascii_uppercase, digits

rooms = {}
def generate_random_room_code(length=4):
    code = "".join(random.choices(ascii_uppercase + digits, k=length))
    if code in rooms:
        return generate_random_room_code(length)
    else:
        rooms[code] = {}
        return code