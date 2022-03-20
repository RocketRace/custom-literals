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

print(10 .s) # 0:00:10
print(1.5.m) # 0:01:30
