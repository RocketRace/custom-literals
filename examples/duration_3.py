from custom_literals import literally
from datetime import timedelta

with literally(float, int, 
    s=lambda x: timedelta(seconds=x), 
    m=lambda x: timedelta(minutes=x), 
    h=lambda x: timedelta(hours=x)
):
    print(10 .s) # 0:00:10
    print(1.5.m) # 0:01:30

assert not hasattr(10, "s")