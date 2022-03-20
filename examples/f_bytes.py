from custom_literals import literal
import re

@literal(bytes, name="f")
def format_bytes(self):
    # this ignores unicode identifiers
    identifier = re.compile(br"\$([a-zA-Z_][a-zA-Z0-9_]*)")
    # this ignores locals & builtins
    names = globals()
    def substitution(match):
        name = match.group(1).decode("utf-8")
        try:
            value = names[name]
        except KeyError:
            raise NameError(f"name '{name}' is not defined")
        if isinstance(value, bytes):
            return value
        try:
            return value.__bytes__()
        except AttributeError:
            return str(value).encode("utf-8")
    return re.sub(identifier, substitution, self)

animal = b"cat"
number = 25

print(b"$animal #$number is the best!".f)
# b"cat #25 is the best!"
