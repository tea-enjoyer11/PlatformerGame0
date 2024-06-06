from pygame import Vector2

v = Vector2(24, 4)
v = v % Vector2(6)  # this doesn't work
v = v % 6  # and his doesn't work
v %= Vector2(6)  # neither does this
v %= 6  # and this

print(v)
