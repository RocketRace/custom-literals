from custom_literals import literal
import textwrap

@literal(str, name="d", strict=True)
def dedented(self):
    return textwrap.dedent(self).strip()

def foo():
    return """
        this multiline string
        looks cleaner in source
    """.d

print(foo())
