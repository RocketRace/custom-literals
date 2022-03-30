'''
A module implementing custom literal suffixes for literal values using pure Python.

(c) RocketRace 2022-present. See LICENSE file for more.

Examples
--------

See the `examples/` directory for more.

Function decorator syntax:
```py
from custom_literals import literal
from datetime import timedelta

@literal(float, int, name="s")
def seconds(self):
    return timedelta(seconds=self)

@literal(float, int, name="m")
def seconds(self):
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
Context manager syntax:
```py
from custom_literals import literally
from datetime import timedelta

with literally(float, int, 
    s=lambda x: timedelta(seconds=x), 
    m=lambda x: timedelta(seconds=60 * x)
):
    print(30 .s + 0.5.m) # 0:01:00
```
'''
from __future__ import annotations
from contextlib import contextmanager

import dis
import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, ContextManager, Generic, Iterator, TypeVar, Union, overload
if TYPE_CHECKING:
    from typing_extensions import Self

import forbiddenfruit

__all__ = (
    "literal",
    "literals",
    "literally",
    "unliteral",
    "rename",
    "is_hooked",
    "lie",
    "ALLOWED_TARGETS"
)

_LOAD_CONST_BYTECODE_OP = dis.opmap["LOAD_CONST"]

ALLOWED_TARGETS = (bool, int, float, complex, str, bytes, None, ...)
ALLOWED_TARGET_TYPES = (bool, int, float, complex, str, bytes, type(None), type(...))

_PrimitiveValue = Union[bool, int, float, complex, str, bytes]
_PrimitiveType = type[_PrimitiveValue]
_NoneType = type(None)
_EllipsisType = type(...)
_SingletonValue = Union[_NoneType, _EllipsisType]

_AllowedValue = Union[_PrimitiveValue, _SingletonValue]
_AllowedType = Union[_PrimitiveType, type[_SingletonValue]]
_AllowedTarget = Union[_PrimitiveType, _SingletonValue]

_LiteralT = TypeVar("_LiteralT", bound=_AllowedValue)
_ReturnT = TypeVar("_ReturnT")

def _to_type(target: _AllowedTarget) -> _AllowedType:
    return target if isinstance(target, type) else type(target)

# Builtin types are static across the interpreter, so active 
# custom literals can be stored globally
_HOOKED_INSTANCES: dict[type, list[str]] = {type: [] for type in ALLOWED_TARGET_TYPES}

class _LiteralDescriptor(Generic[_LiteralT, _ReturnT]):
    def __init__(self, type: type[_LiteralT], /, fn: Callable[[_LiteralT], _ReturnT] , *, name: str, strict: bool):
        if name in _HOOKED_INSTANCES[type]:
            raise AttributeError(f"the custom literal `{name}` is already defined on `{type}` objects")          
        # We are willing to shadow attributes but not to override them directly
        elif name in type.__dict__:
            raise AttributeError(f"the name `{name}` is already defined on `{type}` objects")    
        
        self.type: type[_LiteralT] = type
        self.fn: Callable[[_LiteralT], _ReturnT] = fn
        self.name: str = name
        self.strict: bool = strict
    
    def __get__(self, obj: _LiteralT, owner: type[_LiteralT]) -> _ReturnT | None:
        # When __get__ is called with the arguments
        #    (self, instance, cls)
        # we know that it's being called on an instance,
        # whereas if it's called with the arguments
        #   (self, None, cls)
        # it's being called on the class itself.
        # 
        # Note that there is in fact a glaring ambiguity in this!
        # If cls is NoneType, then instance must be None. Oh no!
        # It's crucial for us to be able to distinguish between
        # __get__ being called on an instance vs being called on
        # the class itself. Otherwise, we can't tell the difference
        # between `hasattr` used to check the existence of an attribute
        # and fetching the attribute itself. As you may guess, this is
        # quite annoying.
        #
        # How do we fix this? There is in fact a solution but it's bad.
        # If we also define a DATA descriptor (any data descriptor) 
        # on type itself in addition to patching our custom literal 
        # descriptor to NoneType, then the new data descriptor will 
        # be given higher priority when calling `NoneType.foo`. That
        # is to say, we can fix the consequences of our monkeypatching
        # with more monkeypatching. As a result of this, we can simply
        # assume that if this __get__ is passed an instance and its type,
        # then it is being accessed directly through the instance.
        if not isinstance(obj, owner):
            return None
        
        if type(obj) is not self.type:
            raise AttributeError(f"the custom literal `{self.name}` of `{owner}` objects is not defined")

        if self.strict:
            current_frame = inspect.currentframe()
            # Running on a different python implementation
            if current_frame is None:
                raise RuntimeError("unreachable")
            
            frame = current_frame.f_back
            # Can only occur if this code is pasted into the global scope
            if frame is None:
                raise RuntimeError("unreachable")

            # We ensure the last executed bytecode instruction 
            # (before the attribute lookup) is LOAD_CONST, i.e.,
            # the object being acted on was just fetched from the 
            # code object's co_consts field. Any other opcode means
            # that the object has been computed, e.g. by storing it
            # in a variable first.
            #
            # Note that this is not forware-compatible due to the
            # possibility of a future change in the bytecode structure
            # and opcode numbering.
            load_instr = frame.f_lasti - 2
            load_kind = frame.f_code.co_code[load_instr]
            if load_kind != _LOAD_CONST_BYTECODE_OP:
                raise TypeError(f"the strict custom literal `{self.name}` of `{self.type}` objects can only be invoked on literal values")
        return self.fn(obj)
    
    # Defined to make this a data descriptor, giving it 
    # higher precedence in attribute lookup. This is *not*
    # required for the patching to work.
    def __set__(self, _obj, _value):
        raise AttributeError

# WARNING
# THIS CLASS IS USED TO FACILITATE AN AWFUL HACK
# THERE IS NO OTHER WORKAROUND AS FAR AS I'M AWARE
# DO NOT TOUCH (the tests will fail if you do)
# 
# For more, check out the big comment block in _LiteralDescriptor.__get__
class _NoneTypeDescriptorHack:
    def __get__(self, obj, type):
        if obj is type(None):
            return None
        raise AttributeError
    def __set__(self, _obj, _value):
        raise AttributeError

_NONE_TYPE_DESCRIPTOR_HACK = _NoneTypeDescriptorHack()

# In the future, these functions may allow customizing the "attack surfact" for 
# builtin attribute hooking. For instance, the __dict__ comparison bug in cpython 
# could be used instead.
def _hook_literal(cls: type[_LiteralT], /, name: str, descriptor: _LiteralDescriptor[_LiteralT, Any]) -> None:
    _HOOKED_INSTANCES[cls].append(name)
    # See the comments in _LiteralDescriptor.__get__
    if cls is type(None):
        forbiddenfruit.curse(type, name, _NONE_TYPE_DESCRIPTOR_HACK)
    forbiddenfruit.curse(cls, name, descriptor)

def _unhook_literal(cls: _AllowedType, /, name: str) -> None:
    forbiddenfruit.reverse(cls, name)
    # See the comments in _LiteralDescriptor.__get__
    if cls is type(None):
        forbiddenfruit.reverse(type, name)
    _HOOKED_INSTANCES[cls].remove(name)

def literal(*targets: _AllowedTarget, name: str | None = None, strict: bool = True) -> Callable[[Callable[[_LiteralT], _ReturnT]], Callable[[_LiteralT], _ReturnT]]:
    '''A decorator defining a custom literal suffix 
    for objects of the given types.

    Examples
    ---------

    ```py
    @literal(str, name="u")
    def utf_8(self):
        return self.encode("utf-8")

    my_string = "hello 😃".u
    print(my_string)
    # b'hello \\xf0\\x9f\\x98\\x83'
    ```

    With multiple target types:
    ```py
    from datetime import timedelta

    @literal(float, int, name="s")
    def seconds(self):
        return timedelta(seconds=self)
    
    @literal(float, int, name="m")
    def minutes(self):
        return timedelta(seconds=60 * self)

    assert (1).m == (30).s + 0.5.m
    ```

    Parameters
    ----------

    *types: type
        The types to define the literal for.
    
    name: str | None
        The name of the literal suffix used, or the name of 
        the decorated function if passed `None`.
    
    strict: bool
        If the custom literal is invoked for objects other than 
        constant literals in the source code, raises `TypeError`.
        By default, this is `True`.

    Raises
    ------

    AttributeError:
        Raised if the custom literal name is already defined as 
        an attribute of the given type.
    '''
    def inner(fn: Callable[[_LiteralT], _ReturnT]) -> Callable[[_LiteralT], _ReturnT]:
        for target in targets:
            type = _to_type(target)
            real_name = fn.__name__ if name is None else name
            # As far as I can tell, there's no way to make this type check properly
            descriptor: _LiteralDescriptor[Any, _ReturnT] = _LiteralDescriptor(type, fn, name=real_name, strict=strict)  # type: ignore
            _hook_literal(type, real_name, descriptor)
        return fn
    return inner

def literals(*targets: _AllowedTarget, strict: bool = True):
    '''A decorator enabling syntactic sugar for class-based
    custom literal definitions. Decorating a class with 
    `@literals(*targets)` is equivalent to decorating each of 
    its methods with `@literal(*targets)`.

    Note: Methods beginning with `__` are ignored, to prevent
    accidental shadowing of builtin methods.
    
    Examples
    ---------

    ```py
    from datetime import timedelta

    @literals(float, int)
    class Duration:
        @rename("h")
        def hours(self):
            return timedelta(seconds=60 * 60 * self)

        @rename("m")
        def minutes(self):
            return timedelta(seconds=60 * self)
        
        @rename("s")
        def seconds(self):
            return timedelta(seconds=self)

    assert 0.5.h + (1).m == (30).m + 60.0.s
    ```

    Parameters
    ----------

    *targets: type
        The types to define the literal for.
    
    strict: bool
        If the custom literal is invoked for objects other than 
        constant literals in the source code, raises `TypeError`.
        By default, this is `True`.
    '''
    def inner(cls: type) -> type:
        for target in targets:
            type = _to_type(target)
            for name in dir(cls):
                fn = getattr(cls, name)
                if not name.startswith("__") and callable(fn):
                    # Check for explicitly renamed methods
                    if isinstance(fn, _RenamedFunction):
                        real_name = fn.name
                    else:
                        real_name = name
                    descriptor = _LiteralDescriptor(type, fn, name=real_name, strict=strict)
                    _hook_literal(type, real_name, descriptor)
        return cls
    return inner

def unliteral(target: _AllowedTarget, /, name: str):
    '''Removes a custom literal from the given type.

    Examples
    --------    

    ```py
    from datetime import datetime

    @literal(int)
    def unix(self):
        return datetime.fromtimestamp(self)

    print(1647804818.unix) # 2022-03-20 21:33:38

    unliteral(int, "unix") 
    assert not hasattr(int, "unix")
    ```

    Parameters
    ----------

    cls: type
        The type to remove the custom literal from.

    name: str
        The name of the custom literal being removed.

    Raises
    ------

    AttributeError:
        Raised when the type does not define a custom literal with the given name.
    
    '''
    type = _to_type(target)
    if name not in _HOOKED_INSTANCES[type]:
        raise AttributeError(f"the custom literal `{name}` of `{type}` objects is not defined")
    
    _unhook_literal(type, name=name)

@contextmanager
def literally(*targets: _AllowedTarget, strict: bool = True, **fns: Callable[[_LiteralT], Any]) -> Iterator[None]:
    '''A context manager for temporarily defining custom literals.

    Note: Due to the overlap in function signature, it is not possible to use
    `literally` to define a custom literal named `strict`. To avoid this,
    you can manually hook and unhook your custom literal using `@literal` and
    `@unliteral` respectively.

    Examples
    --------

    ```py
    from datetime import datetime

    with literally(int, unix=datetime.fromtimestamp):
        print((1647804818).unix) # 2022-03-20 21:33:38
    ```

    Parameters
    ----------

    *targets: type
        The types to define the literals for.

    strict: bool
        If the custom literal is invoked for objects other than
        constant literals in the source code, raises `TypeError`.
        By default, this is `True`.

    **fns: (type -> Any)
        The functions to call when the literal is invoked. The name
        of the keyword argument is used as the name of the custom literal.

    Raises
    ------

    AttributeError:
        Raised if the custom literal name is already defined as
        an attribute of the given type.
    '''
    types = [_to_type(target) for target in targets]
    for type in types:
        for name, fn in fns.items():
            descriptor = _LiteralDescriptor(type, fn, name=name, strict=strict)
            _hook_literal(type, name, descriptor)
    yield
    for type in types:
        for name in fns:
            _unhook_literal(type, name=name)

def is_hooked(target: _AllowedTarget, /, name: str) -> bool:
    '''Returns whether the given custom literal is 
    hooked in the given type.

    Examples
    --------

    ```py
    from datetime import datetime

    @literal(int)
    def unix(self):
        return datetime.fromtimestamp(self)

    print(is_hooked(int, "unix")) # True
    ```

    Parameters
    ----------

    target: type
        The type to check.

    name: str
        The name of the custom literal.

    Returns
    -------

    bool
        Whether the given custom literal is hooked.
    '''
    return name in _HOOKED_INSTANCES[_to_type(target)]

class _RenamedFunction(Generic[_LiteralT, _ReturnT]):
    # To signal that a function has been renamed.
    # This is necessary because the `__name__` attribute
    # of a method can be different from its name in the
    # class dirs for multiple reasons, and we need to
    # be able to tell when that has happened as a result
    # of the `rename` decorator.
    def __init__(self, fn: Callable[[_LiteralT], _ReturnT], name: str):
        self.fn = fn
        self.name = name
    
    def __call__(self, arg: _LiteralT) -> _ReturnT:
        return self.fn(arg)

def rename(name: str) -> Callable[[Callable[[_LiteralT], _ReturnT]], Callable[[_LiteralT], _ReturnT]]:
    '''A utility decorator for renaming functions. Useful when combined
    with class-based custom literal definitions using `literals`.

    Examples
    --------

    ```py
    @literals(str)
    class CaseLiterals:
        @rename("u")
        def uppercase(self):
            return self.upper()
        @rename("l")
        def lowercase(self):
            return self.lower()

    print("Hello, World!".u) # HELLO, WORLD!
    print("Hello, World!".l) # hello, world!
    ```

    Parameters
    ----------
    
    name: str
        The updated name.
    '''
    def inner(fn: Callable[[_LiteralT], _ReturnT]) -> Callable[[_LiteralT], _ReturnT]:
        return _RenamedFunction(fn, name)
    return inner

def lie(target: type[_LiteralT], /) -> type[_LiteralT]:
    '''A utility function for lying to type checkers.
    Useful in conjunction with class-based custom literals
    using `@literals`, since the type checker cannot infer
    the type of `self` in methods to be compatible with
    the target types.

    The signature of this function is a lie. It does not actually
    return the input type, but instead returns `object`. This 
    makes it a no-op when used as the base class in a class definition,
    whilst tricking some static analysis tools into thinking that
    the resulting class is a subclass of the input type.

    Examples
    --------
    ```py
    @literals(int)
    class Naughty(lie(int)):
        # lie is marked to return `int`, meaning
        # `self` is assumed to subclass `int`.
        @rename("s")
        def successor(self):
            # type checkers may otherwise complain that
            # `Naughty + int` is not a valid operation.
            return self + 1
    ```

    Parameters
    ----------

    target: type
        The type to lie about.
    '''
    # this type-ignore comment cannot be removed, by design
    return object # type: ignore
