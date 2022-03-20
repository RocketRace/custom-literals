from custom_literals import Literal
from datetime import timedelta

class Duration(Literal, float, int):
    # Alternatively, @rename("s") on a 
    # differently named function
    def s(self):
        return timedelta(seconds=self)
    def m(self):
        return timedelta(seconds=60 * self)
    def h(self):
        return timedelta(seconds=3600 * self)

# int is a child of float, so it's allowed
print(10 .s)
print(1.5.m)
# unintuitively, bool is also allowed since
# it's a direct subclass of int
print(True.h)
