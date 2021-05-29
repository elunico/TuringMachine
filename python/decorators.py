import dataclasses
from functools import reduce


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
