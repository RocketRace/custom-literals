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

print(10 .s) # 0:00:10
print(1.5.m) # 0:01:30

