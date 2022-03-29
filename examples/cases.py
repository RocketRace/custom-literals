from custom_literals import literals

@literals(str, bytes)
class CaseLiterals:
    def u(self):
        return self.upper()
    def l(self):
        return self.lower()

print("Hello, World!".u) # HELLO, WORLD!
print(b"Hello, World!".l) # b"hello, world!""
