custom_literals
===============

A module implementing custom literal suffixes using pure Python. `custom_literals` 
mimics C++'s user-defined literals (UDLs) by defining literal suffixes that can 
be accessed as attributes of literal values, such as numeric constants, string 
literals and more.

(c) RocketRace 2022-present. See LICENSE file for more.

Examples
========

See the `examples/` directory for more.

Function decorator syntax:
```py
from custom_literals import literal
from datetime import timedelta

@literal(float, int, name="s")
def seconds(self):
    return timedelta(seconds=self)

@literal(float, int, name="m")
def minutes(self):
    return timedelta(seconds=60 * self)

print(30 .s + 0.5.m) # 0:01:00
```
Class decorator syntax:
```py
from custom_literals import literals
from datetime import timedelta

@literals(float, int)
class Duration:
    def s(self):
        return timedelta(seconds=self)
    def m(self):
        return timedelta(seconds=60 * self)

print(30 .s + 0.5.m) # 0:01:00
```
Removing a custom literal:
```py
from custom_literals import literal, unliteral

@literal(str)
def u(self):
    return self.upper()

print("hello".u) # "HELLO"

unliteral(str, "u")
assert not hasattr("hello", "u")
```
Context manager syntax (automatically removes literals afterwards):
```py
from custom_literals import literally
from datetime import timedelta

with literally(float, int, 
    s=lambda x: timedelta(seconds=x), 
    m=lambda x: timedelta(seconds=60 * x)
):
    print(30 .s + 0.5.m) # 0:01:00
```

Features
========

Currently, three methods of defining custom literals are supported:
The function decorator syntax `@literal`, the class decorator syntax `@literals`, and the
context manager syntax `with literally`. (The latter will automatically unhook the literal
suffixes when the context is exited.) To remove a custom literal, use `unliteral`.

Custom literals are defined for literal values of the following types:

| Type | Example | Notes |
|------|---------|-------|
| `int` | `(42).x` | The Python parser interprets `42.x` as a float literal followed by an identifier. To avoid this, use `(42).x` or `42 .x` instead. |
| `float` | `3.14.x` | |
| `complex` | `1j.x` | |
| `bool` | `True.x` | Since `bool` is a subclass of `int`, `int` hooks may influence `bool` as well. |
| `str` | `"hello".x` | F-strings (`f"{a}".x`) are also supported. |
| `bytes` | `b"hello".x` | |
| `None` | `None.x` | |
| `Ellipsis` | `....x` | Yes, this is valid syntax. |
| `tuple` | `(1, 2, 3).x` | Generator expressions (`(x for x in ...)`) are not tuple literals and thus won't be affected by literal suffixes. |
| `list` | `[1, 2, 3].x` | List comprehensions (`[x for x in ...]`) may not function properly. |
| `set` | `{1, 2, 3}.x` | Set comprehensions (`{x for x in ...}`) may not function properly. |
| `dict` | `{"a": 1, "b": 2}.x` | Dict comprehensions (`{x: y for x, y in ...}`) may not function properly. |

In addition, custom literals can be defined to be *strict*, that is, only allow the given 
literal suffix to be invoked on constant, literal values. This means that the following 
code will raise a `TypeError`:

```py
@literal(str, name="u", strict=True)
def utf_8(self):
    return self.encode("utf-8")

my_string = "hello"
print(my_string.u) 
# TypeError: the strict custom literal `u` of `str` objects can only be invoked on literal values
```

By default, custom literals are *not* strict. This is because determining whether a suffix was
invoked on a literal value relies on bytecode analysis, which is a feature of the CPython
interpreter, and is not guaranteed to be forwards compatible. It can be enabled by passing 
`strict=True` to the `@literal`, `@literals` or `literally` functions.

Caveats
========

Stability
---------

This library relies almost entirely on implementation-specific behavior of the CPython
interpreter. It is not guaranteed to work on all platforms, or on all versions of Python.
It has been tested on common platforms (windows, ubuntu, macos) using python 3.7 through
to 3.10, but while changes that would break the library are quite unlikely, they are not
impossible either.

**That being said,** `custom_literals` does its absolute best to guarantee maximum 
stability of the library, even in light of possible breaking changes in CPython internals.
The code base is well tested. In the future, the library may also exposes multiple 
different backends for the actual implementation of builtin type patching. As of now,
the only valid backend is `forbiddenfruit`, which uses the `forbiddenfruit` library.

Type safety
-----------

The library code, including the public API, is fully typed. Registering and unregistering
hooks is type-safe, and static analysis tools should have nothing to complain about.

However, accessing custom literal suffixes is impossible to type-check. This is because
all major static  analysis tools available for python right now (understandably) assume 
that builtins types are immutable. That is, the attributes and methods builtin types 
cannot be dynamically modified. This goes against the core idea of the library, which 
is to patch custom attributes on builtin types. 

Therefore, if you are using linters, type checkers or other static analysis tools, you 
will likely encounter many warnings and errors. If your tool allows it, you should disable 
these warnings (ideally on a per-diagnostic, scoped basis) if you want to use this library 
without false positives.

FAQ
=====

Should I use this in production?
-------------------------------

Emphatically, no! But I won't stop you.

Why?
-----

Python's operator overloading allows for flexible design of domain-specific languages. 
However, Python pales in comparison to C++ in this aspect. In particular, User-Defined 
Literals (UDLs) are a powerful feature of C++ missing in Python. This library is designed
to emulate UDLs in Python, with syntactic sugar comparable to C++ in elegance.

But *really*, why?
-------------------

Because it's posssible.

Nooooooo (runs away from computer)
----------------------------------

I kind of disagree: yessss (dances in front of computer)

Could this ever be type safe?
-----------------------------

I doubt it. The assumptions made by static analysis tools are incredibly useful, and
this is such an edge case it makes no sense for them to assume builtin literal types can have
dynamically set attributes. In addition, there isn't a good way to signal to your type 
checker that an immutable type is going to be endowed with new attributes!

License
=======

(c) RocketRace 2022-present. This library is under the Mozilla Public License 2.0. 
See the `LICENSE` file for more details.

Contributing
============

Patches, bug reports, feature requests and pull requests  are welcome.

Links
=====

* [GitHub repository](https://github.com/RocketRace/custom_literals)
