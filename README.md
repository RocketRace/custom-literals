`custom-literals`
===============

A module implementing custom literal suffixes using pure Python. `custom-literals` 
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

**That being said,** `custom-literals` does its absolute best to guarantee maximum 
stability of the library, even in light of possible breaking changes in CPython internals.
The code base is well tested. In the future, the library may also expose multiple 
different backends for the actual implementation of builtin type patching. As of now,
the only valid backend is `forbiddenfruit`, which uses the `forbiddenfruit` library.

| Feature | Stability |
|---------|-----------|
| Hooking with the `forbiddenfruit` backend | Quite stable, but may be affected by future releases. Relies on the `ctypes` module. |
| Strict mode using the `strict=True` kwarg | Quite stable, but not forwards compatible. Relies on stack frame analysis and opcode checks to detect non-literal access. |

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

Nooooooo (runs away from computer)
----------------------------------

I kind of disagree: yessss (dances in front of computer)

Why?
-----

Python's operator overloading allows for flexible design of domain-specific languages. 
However, Python pales in comparison to C++ in this aspect. In particular, User-Defined 
Literals (UDLs) are a powerful feature of C++ missing in Python. This library is designed
to emulate UDLs in Python, with syntactic sugar comparable to C++ in elegance.

But *really*, why?
-------------------

Because it's posssible.

How? (please keep it short)
--------------------------

`custom-literals` works by patching builtin types with custom objects satisfying the 
[descriptor protocol](https://docs.python.org/3/howto/descriptor.html), similar to 
the builtin `property` decorator. The patching is done trough a "backend", which 
is an interface implementing functions to mutate the `__dict__` of builtin types. 
If `strict=True` mode is enabled, the descriptor will also traverse stack frames 
backwards to the invokation site of the literal suffix, and check the most recently 
executed bytecode opcode to ensure that the literal suffix was invoked on a literal value.

How? (I love detail)
---------------------

Builtin types in CPython are implemented in C, and include checks to prevent
mutation at runtime. This is why the following lines will each raise a `TypeError`:

```py
int.x = 42 # TypeError: cannot set 'x' attribute of immutable type 'int'
setattr(int, "x", 42) # TypeError: cannot set 'x' attribute of immutable type 'int'
int.__dict__["x"] = 42 # TypeError: 'mappingproxy' object does not support item assignment
```

However, these checks can be subverted in a number of ways. One method is to use
CPython's APIs directly to bypass the checks. For the sake of stability, `custom-literals`
calls the `curse()` and `reverse()` functions of the `forbiddenfruit` library
to implement these bypasses. Internally, `forbiddenfruit` uses the `ctypes` module
to access the C API and use the `ctypes.pythonapi.PyType_Modified()` function to
signal that a builtin type has been modified. Other backends may also be available in the future, 
but are not implemented at the moment. (As an example, there is currently a bug 
in CPython that allows `mappingproxy` objects to be mutated without using `ctypes`. 
This was deemed too fragile to be included in the library.)

Python's [`@property`](https://docs.python.org/3/howto/descriptor.html#properties) decorator
implements the [descriptor protocol](https://docs.python.org/3/howto/descriptor.html).
This is a protocol that allows for custom code to be executed when accessing specific
attributes of a type. For example, the following code will print `42`:

```py
class MyClass:
    @property
    def x(self):
        print(42)

MyClass().x
```

`custom-literals` patches builtin types with objects implementing the same protocol, 
allowing for user-defined & library-defiend code to be executed when invoking a literal
suffix on a builtin type. It cannot however use `@property` directly, as elaborated
below.

The descriptor protocol is very flexible, used as the the backbone of bound methods, 
class methods, and static methods and more. It is defined by the presence of one
of the following methods\*:

```py
class SomeDescriptor:
    # <instance>.<attribute>
    def __get__(self, instance, owner) -> value: ...
    # <instance>.<attribute> = <value>
    def __set__(self, instance, value) -> None: ...
    # del <instance>.<attribute>
    def __delete__(self, instance) -> None: ...
```

\**and optionally [`__set_name__`](https://docs.python.org/3/reference/datamodel.html#object.__set_name__)*

The descriptor methods can be invoked from an instance (`some_instance.x`) or from
a class (`SomeClass.x`). Importantly for us, the `__get__` method is called with 
different arguments depending on whether the descriptor is accessed from an instance
or a class:
    
```py
class MyDesciptor:
    def __get__(self, instance, owner) -> value:
        print(f"Instance: {instance}")
        print(f"Owner: {owner}")

class MyClass:
    x = MyDesciptor()

MyClass().x 
# Instance: <__main__.MyClass object at 0x110e3a170> 
# Owner: <class '__main__.MyClass'>
MyClass.x 
# Instance: None 
# Owner: <class '__main__.MyClass'>
```

This is used to differentiate between the two cases. `@property`'s implementation
simply returns the descriptor instance if `instance` is `None`, which is a fair
test for whether the descriptor is accessed from a class or an instance.

Keen-eyed readers may notice however that this is not a perfect test. What if `MyClass`
is somehow `type(None)`? In this case, the two cases will be indistinguishable. 
In normal code, this is not a problem, as `type(None)` is a builtin type, and
thus cannot be mutated. In `custom-literals`, however, this breaks custom literals
that are defined on `type(None)`. 

This can thankfully be mitigated thanks to the concept of a 
[data descriptor](https://docs.python.org/3/howto/descriptor.html#data-descriptors).
A data descriptor is a descriptor that defines `__set__` or `__delete__`. When 
Python tries to resolve attribute access on an instance, it will first check whether
its *type* has a data descriptor for the attribute, overriding any descriptors 
defined on the *instance* itself. For example, suppose the following example using
a metaclass (a class inheriting from `type`):

```py
class DataDescriptor:
    def __get__(self, instance, owner):
        print("The data descriptor was called!")
        print(f"Instance: {instance}")
    
    # Simply the presence of the method is enough
    # to convert this into a data descriptor
    def __set__(self, instance, value):
        raise AttributeError

class NormalDescriptor:
    def __get__(self, instance, owner):
        print("The normal descriptor was called!")
        print(f"Instance: {instance}")

class MyMeta(type):
    x = DataDescriptor()

class MyClass(metaclass=MyMeta):
    x = NormalDescriptor()

MyClass.x 
# The data descriptor was called!
# Instance: <class '__main__.MyClass'>
MyClass().x 
# The normal descriptor was called!
# Instance: <__main__.MyClass object at 0x10f468ee0>s
```

This example shows that it is possible to ensure that a descriptor is always
called on an instance with `instance` set to an instance of the class. In the case of
`custom-literals`, this is achieved by patching a data descriptor (any data descriptor)
on `type` when `type(None)` is also being patched. This removes the ambiguity of
whether the descriptor is called on an instance or a class. Yay!

Finally, `custom-literals` also provides a mechanism for optionally detecting when a custom 
literal suffix is invoked on a constant and literal type. (This is invoked when the
`strict` argument is set to `True`.) This is achieved by attaching
extra code to the `__get__` method of the custom literal descriptor. The code performs
*bytecode analysis* at the invocation site of the custom literal suffix.

The CPython interpreter uses stack frames to implement function calls. When a function is
called, a new frame is created and pushed to the stack, and when the function returns, the
frame is popped off the stack. Importantly, these frame objects can be accessed directly
from Python:

```py
import inspect

def foo():
    local_variable = 123
    bar()

def bar():
    # Alternatively, use `sys._getframe()`
    frame = inspect.currentframe()
    # The `f_back` attribute of a frame object
    # points to the frame that called it
    previous_frame = frame.f_back
    # Frame objects have information about the
    # invocation context of the frame, including
    # e.g. local variables
    previous_locals = previous_frame.f_locals
    print(previous_locals['local_variable']) # 123
```

The `f_code` attribute of a frame object contains information about the bytecode of the
currently executed code. CPython being an interpreter, this bytecode corresponds roughly
to the source code of the function. For example, see the disassembly of the following:

```py
import dis

def add(a, b):
    c = a + b
    return int(c)

dis.dis(add) # Outputs:
# 4           0 LOAD_FAST                0 (a)
#             2 LOAD_FAST                1 (b)
#             4 BINARY_ADD
#             6 STORE_FAST               2 (c)
# 
# 5           8 LOAD_GLOBAL              0 (int)
#            10 LOAD_FAST                2 (c)
#            12 CALL_FUNCTION            1
#            14 RETURN_VALUE
```

* First, the two arguments `a` and `b` are pushed onto the stack.
* The arguments are popped from the stack and used as the operands for `+`. The result is pushed onto the stack.
* The top of the stack is popped and stored in a local variable `c`.
* The `int` function is fetched from the global namespace and pushed to the stack.
* The local variable `c` is pushed to the stack.
* The `int` function is called with one argument, and the return value of `int` is pushed to the stack.
* The result is popped from the stack and returned.

In the case of custom literals, the opcodes we are concerned about are the following:

* `LOAD_CONST`, used to load a constant (including most literal values) to the stack
* `BUILD_TUPLE`/`BUILD_LIST`/`BUILD_SET`/`BUILD_MAP`, used to push tuple/list/set/dict literals to the stack
* `FORMAT_VALUE`, used to push a formatted f-string literal (`f"{a} {b} {c}"`) to the stack
* `LIST_TO_TUPLE`/`LIST_EXTEND`/`SET_UPDATE`/`DICT_UPDATE`, sometimes used in list/set/dict literals, for example when using the star unpack syntax (`[a, b, c, *x]`)

(Do keep in mind that opcodes are not necessarily forwards compatible. Python 3.11 could release
a dozen new opcodes tomorrow that need to be accounted for by the library! This is why 
`custom-literals` does not perform bytecode analysis by default.)

If strict mode is enabled, the library will traverse up through the stack frames, inspect the bytecode,
check the most recently executed opcode (available in `frame.f_lasti`), and check if it is one of the
opcodes listed above. If the opcode is not in the allowed list, an error is raised, which is why
the following code raises an error:

```py
@literal(str, strict=True)
def xyz(self):
    return 123

abc = "abc"
abc.xyz 
# TypeError: the strict custom literal `xyz` of `str` objects can only be invoked on literal values
```

Putting all of these features together, `custom-literals` is able to do the seemingly impossible - 
define custom literal suffixes on builtin types that can only be invoked on literal values!

Making this project has been a fascinating deep dive into some of the internals of CPython, and 
I hope it has been equally interesting to you, the reader.

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

* [GitHub repository](https://github.com/RocketRace/custom-literals)
* [PyPI](https://pypi.org/project/custom-literals/)
