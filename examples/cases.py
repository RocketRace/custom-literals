from custom_literals import Literal, rename

class CaseLiterals(Literal, str, bytes):
    # equivalent to def u(self): ...
    @rename("u")
    def uppercase(self):
        return self.upper()
    # equivalent to def l(self): ...
    @rename("l")
    def lowercase(self):
        return self.lower()

print("Hello, World!".u) # HELLO, WORLD!
print(b"Hello, World!".l) # b"hello, world!""
