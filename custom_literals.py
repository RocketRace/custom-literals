'''
A module implementing custom literal suffixes for literal values using pure Python.

(c) RocketRace 2022-present. See LICENSE file for more.
'''
from __future__ import annotations

import dis
import inspect
from typing import Any, Callable, Generic, TypeVar

import forbiddenfruit

__all__ = (
    "literal",
    "Literal",
    "rename",
    "unliteral",
)

_LOAD_CONST = dis.opmap["LOAD_CONST"]

_TargetT = TypeVar("_TargetT", bool, int, float, complex, str, bytes)
_ReturnT = TypeVar("_ReturnT")

class _LiteralDescriptor(Generic[_TargetT, _ReturnT]):
    def __init__(self, type: type[_TargetT], /, fn: Callable[[_TargetT], _ReturnT], *, name: str, strict: bool):
        if hasattr(type, name):
            raise AttributeError(f"The name {name} is already defined on objects of type {type.__qualname__}")
        
        self.cls: type[_TargetT] = type
        self.fn: Callable[[_TargetT], _ReturnT] = fn
        self.name: str = name
        self.strict: bool = strict
    
    def __get__(self, obj: _TargetT, _owner=None) -> _ReturnT:
        if self.strict:
            if type(obj) is not self.cls:
                raise TypeError(f"the custom literal `{self.cls.__qualname__}.{self.name}` with `final=True` cannot be applied to values of type `{type(obj).__qualname__}`")

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
            load_instr = frame.f_lasti - 2
            load_kind = frame.f_code.co_code[load_instr]
            if load_kind != _LOAD_CONST:
                raise TypeError(f"the strict custom literal `{self.cls.__qualname__}.{self.name}` cannot be applied to computed values")
        return self.fn(obj)
    
    # Defined to make this a data descriptor,
    # giving it higher precedence in attribute lookup
    def __del__(self, _obj: _TargetT, _owner=None):
        raise AttributeError

# In the future, these functions may allow customizing the "attack surfact" for 
# builtin attribute hooking. For instance, the __dict__ comparison bug in cpython 
# could be used instead.
def _hook_literal(cls: type[_TargetT], /, name: str, descriptor: _LiteralDescriptor[_TargetT, Any]) -> None:
    forbiddenfruit.curse(cls, name, descriptor)

def _unhook_literal(cls: type[_TargetT], /, name: str) -> None:
    forbiddenfruit.reverse(cls, name)

def literal(*types: type[_TargetT], name: str | None = None, strict: bool = True) -> Callable[[Callable[[_TargetT], _ReturnT]], Callable[[_TargetT], _ReturnT]]:
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
        The type to define the literal for.
    
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
    def inner(fn: Callable[[_TargetT], _ReturnT]) -> Callable[[_TargetT], _ReturnT]:
        for type in types:
            fn_name = fn.__name__ if name is None else name
            descriptor = _LiteralDescriptor(type, fn, name=fn_name, strict=strict)
            _hook_literal(type, fn_name, descriptor)
        return fn
    return inner

class _LiteralMeta(type):
    # This needs to be done in __new__ since it 
    # manipulates the bases i.e. the MRO
    def __new__(cls: type, name: str, bases: tuple[type, ...], ns: dict[str, Any], **kwargs):
        if bases != ():
            # The target types are stripped from the bases, so they 
            # have to be stored elsewhere. The other alternative
            # to an attribute is to pass it as a kwarg, but it would
            # become part of the public API which is undesirable.
            types = list(bases)
            types.remove(Literal)
            setattr(cls, "_types", tuple(types))
            return super().__new__(cls, name, (Literal,), ns, **kwargs)
        return super().__new__(cls, name, bases, ns)

class Literal(metaclass=_LiteralMeta):
    '''Syntactic sugar enabling class-based custom literal definitions.
    This should be used exclusively for subclassing, and arguments should
    be passed to the class definition. In essence, the definition 
    `class Foo(Literal, *targets, **kwargs): ...` applies the decorator 
    `@literal(*targets, **kwargs)` on each of the methods defined by the
    class.

    Examples
    --------

    ```py
    from datetime import timedelta

    class Duration(Literal, float, int):
        def s(self):
            return timedelta(seconds=self)
        def m(self):
            return timedelta(seconds=60 * self)
        def h(self):
            return timedelta(seconds=3600 * self)
    
    print(10 .s) # 0:00:10
    print(1.5.m) # 0:01:30
    print((2).h) # 2:00:00
    ```

    Parameters
    ----------

    *<target_types>: type
        The types to define the custom literals for. These is passed as base classes
        to the class definition: `class MyClass(Literal, type_0, type_1, ...): ...`

    strict: bool
        A kwarg determining whether `TypeError` is raised 
        when the custom literals are invoked for objects other than constant 
        literals in the source code. By default, this is `True`.

    Raises
    ------

    AttributeError:
        Raised if any of the custom literals names are already defined as 
        attributes of the given type.
    '''
    _types: tuple[type, ...]
    @classmethod
    def __init_subclass__(cls, *, strict: bool = True) -> None:
        super().__init_subclass__()
        for name, fn in vars(cls).items():
            # Allows functions, lambdas, and other common callables
            if callable(fn):
                for type in cls._types:
                    # The assigned name is used here instead of introspecting
                    # the callable object, as lambdas are both callable and 
                    # instances of FunctionTypes, but their
                    # __name__ is still not a valid Python identifier.
                    descriptor = _LiteralDescriptor(type, fn, name=name, strict=strict)
                    _hook_literal(type, name, descriptor)

def unliteral(cls: type[_TargetT], /, name: str):
    '''Removes a custom literal from the given type.

    Examples
    --------    

    ```py
    from datetime import datetime

    @literal(int)
    def unix(self):
        return datetime.fromtimestamp(self)

    print(1647804818.unix) # 2022-03-20 17:33:38

    unliteral(int, "unix")    
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
        Raised when the given type does not have the provided name as an attribute.
        
    TypeError:
        The attribute is defined on the type, but it is not a custom literal.
    '''
    if not hasattr(cls, name):
        raise AttributeError(f"the literal `{cls.__qualname__}.{name}` is not defined")
    
    descriptor = cls.__dict__.get(name)
    if not isinstance(descriptor, _LiteralDescriptor):
        raise TypeError(f"the attribute `{cls.__qualname__}.{name}` is not a custom literal")
    
    _unhook_literal(cls, name=name)

def rename(name: str) -> Callable[[Callable[[_TargetT], _ReturnT]], Callable[[_TargetT], _ReturnT]]:
    '''A utility decorator for renaming functions. Useful when combined
    with class-based custom literal definitions using `Literal`.

    Examples
    --------

    ```py
    class CaseLiterals(Literal, str):
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
    def inner(fn: Callable[[_TargetT], _ReturnT]) -> Callable[[_TargetT], _ReturnT]:
        fn.__name__ = name
        return fn
    return inner
