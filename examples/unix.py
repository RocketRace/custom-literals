from custom_literals import literally
from datetime import datetime

with literally(int, unix=datetime.fromtimestamp):
    print((1647804818).unix) # 2022-03-20 21:33:38

assert not hasattr(1647804818, "unix")
