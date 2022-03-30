from custom_literals import literal

@literal(set, name="f")
def as_frozenset(self):
    return frozenset(self)

assert {1, 2, 3, 4}.f == frozenset({1, 2, 3, 4})