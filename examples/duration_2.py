from custom_literals import literals, lie, rename
from datetime import timedelta

@literals(float, int)
class Duration(lie(float)):
    @rename("s")
    def seconds(self):
        return timedelta(seconds=self)
    @rename("m")
    def minutes(self):
        return timedelta(seconds=60 * self)
    @rename("h")
    def hours(self):
        return timedelta(seconds=3600 * self)

print(10 .s) # 0:00:10
print(1.5.m) # 0:01:30
