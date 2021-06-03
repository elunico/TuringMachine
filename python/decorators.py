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


# used for accepts when type is type of class being defined
class Self(type):
    pass


def _isiterable(t):
    try:
        i = iter(t)
        return True
    except TypeError:
        return False


# from PEP 318 with heavy modifications
def accepts(*types: Union[type, Tuple[type]]):
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
