from custom_literals import literal
from datetime import timedelta

@literal(float, int, name="s")
def seconds(self):
    return timedelta(seconds=self)

@literal(float, int, name="m")
def minutes(self):
    return timedelta(seconds=60 * self)

@literal(float, int, name="h")
def hours(self):
    return timedelta(seconds=3600 * self)

# int is a child of float, so it's allowed
print(15 .s)
print(0.75.m)
# unintuitively, bool is also allowed since
# it's a direct subclass of int
print(True .h)
