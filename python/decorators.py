import dataclasses
import enum
import functools
import inspect
from functools import reduce
from typing import Tuple, Union


# taken from https://stackoverflow.com/questions/3589311/get-defining-class-of-unbound-method-object-in-python-3
def _get_class_that_defined_method(meth):
    if isinstance(meth, functools.partial):
        return _get_class_that_defined_method(meth.func)
    if inspect.ismethod(meth) or (
            inspect.isbuiltin(meth) and getattr(meth, '__self__', None) is not None and getattr(meth.__self__,
                                                                                                '__class__', None)):
        for cls in inspect.getmro(meth.__self__.__class__):
            if meth.__name__ in cls.__dict__:
                return cls
        meth = getattr(meth, '__func__', meth)  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0],
                      None)
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


class Self(type):
    """
    This class stands in for the type of the class being defined. Since decorators require evaluation
    before the defintion end of a class, you cannot use a class's type in the @accepts for one of its
    methods. Instead, you should use the type Self. This will be replaced by the class type at runtime.
    This does not make sense for unbound methods (free functions) or static methods and will raise an
    error if passed to such a function or method.

    Example:

        class Vector2D:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z

            @accepts(Self)
            def plus(self, other):
                self.x += other.x
                self.y += other.y
                self.z += other.z

         class State:
            registry = {}

            @classmethod
            @accepts((Self, str))
            def get(cls, s):
                if isinstance(s, State):
                    return s
                else:
                    if s not in registry:
                        registry[s] = State(s)
                    return registry[s]

            @accepts(str)
            def __init__(self, name):
                self.name = name
    """
    pass


def _isiterable(t):
    try:
        i = iter(t)
        return True
    except TypeError:
        return False


# from PEP 318 with heavy modifications
def accepts(*types: Union[type, Tuple[type]]):
    """
    Provides a declaration and run-time check of the types accepted by a function or method

    Pass 1 type per argument or, if multiple types are acceptable, 1 tuple of types per argument (as used in isinstance)

    DO NOT PASS A TYPE FOR self OR cls parameters. The parameters 'self' and 'cls' are NEVER CHECKED by if they appear
    as the first parameter in a method.

    :param types: a splat of types or tuples of types to match 1 to 1 against the args to the function
    :return: a decorator which wraps a function and does a run time type check on all arguments against the types
             given EXCEPT for 'self' and 'cls' first args
    """
    def check_accepts(f):
        is_bound = len(f.__code__.co_varnames) > 0 and (
                f.__code__.co_varnames[0] == 'self' or f.__code__.co_varnames[0] == 'cls')
        if is_bound:
            argcount = f.__code__.co_argcount - 1
        else:
            argcount = f.__code__.co_argcount
        assert len(types) == argcount, "Not enough types for arg count, expected {} but got {}".format(argcount,
                                                                                                       len(types))

        @functools.wraps(f)
        def new_f(*args, **kwds):
            if is_bound:
                for_args = args[1:]  # drop self or cls
            else:
                for_args = args
            for (a, t) in zip(for_args, types):
                if _isiterable(t) and not isinstance(t, enum.EnumMeta):
                    t = tuple([_get_class_that_defined_method(f) if i is Self else i for i in t])
                    assert all(i is not None for i in t), "Cannot accept Self on non-bound method {}".format(f.__name__)
                else:
                    t = _get_class_that_defined_method(f) if t is Self else t
                    assert t is not None, "Cannot accept Self on non-bound method {}".format(f.__name__)
                assert isinstance(a, t), "{}: got argument {} (type of {}) but expected argument of type(s) {}".format(
                    f.__name__, a, type(a), t)
            return f(*args, **kwds)

        return new_f

    return check_accepts


# decorator function
def stringable(cls):
    def __str__(self):
        items = ['{}={}'.format(k, v) for (k, v) in self.__dict__.items()]
        items_string = ', '.join(items)
        return '{}[{}]'.format(self.__class__.__name__, items_string)

    setattr(cls, '__str__', __str__)
    setattr(cls, '__repr__', __str__)
    return cls


def equatable(cls):
    def __eq__(self, other):
        if type(other) is not type(self):
            return False
        pairs = zip(self.__dict__.values(), other.__dict__.values())
        return all([i[0] == i[1] for i in pairs])

    setattr(cls, '__eq__', __eq__)
    setattr(cls, '__hash__', None)
    return cls


def hashable(cls):
    cls = equatable(cls)

    def hasher(a, i):
        return ((a << 8) | (a >> 56)) ^ hash(i)

    def __hash__(self):
        for (name, value) in self.__dict__.items():
            if type(value).__hash__ is None:
                fmt_str = "value of type {} can't be hashed because the field {}={} (type={}) is not hashable"
                str_format = fmt_str.format(repr(cls.__name__), repr(name), repr(value), repr(type(value).__name__))
                raise TypeError(str_format)
        return super(cls, self).__hash__() ^ reduce(hasher, self.__dict__.values(), 0)

    setattr(cls, '__hash__', __hash__)
    return cls


# decorator function
def dataclass(cls):
    cls = dataclasses.dataclass(cls, init=True, repr=True, eq=True, frozen=True)
    cls = stringable(cls)
    return cls
