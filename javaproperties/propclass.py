import collections
from   six      import string_types
from   .reading import load
from   .util    import strify_dict
from   .writing import dump
from   .xml     import load_xml, dump_xml

# https://docs.oracle.com/javase/8/docs/api/java/util/Properties.html

_type_err = 'Keys & values of Properties objects must be strings'

class Properties(collections.MutableMapping):
    """ TODO """

    def __init__(self, data=None, defaults=None):
        """ TODO """
        # `defaults` must be a Properties object
        self.data = {}
        if data is not None:
            self.data.update(strify_dict(data))
        self.defaults = defaults

    def __getitem__(self, key):
        if not isinstance(key, string_types):
            raise TypeError(_type_err)
        return self.data[key]

    def __setitem__(self, key, value):
        if not isinstance(key, string_types) or \
                not isinstance(value, string_types):
            raise TypeError(_type_err)
        self.data[key] = value

    def __delitem__(self, key):
        if not isinstance(key, string_types):
            raise TypeError(_type_err)
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return '{__class__.__name__}({data!r}, defaults={defaults!r})'\
                .format(**dir(self))

    def __eq__(self, other):
        return type(self) is type(other) and \
                self.data == other.data and \
                self.defaults == other.defaults

    def __ne__(self, other):
        return not (self == other)

    def __nonzero__(self):
        return bool(self.data)

    __bool__ = __nonzero__

    def getProperty(self, key, defaultValue=None):
        """ TODO """
        try:
            return self[key]
        except KeyError:
            if self.defaults is not None:
                return self.defaults.getProperty(key, defaultValue)
            else:
                return defaultValue

    def load(self, fp):
        """ TODO """
        self.data.update(load(fp))

    def propertyNames(self):
        """ TODO """
        for k in self.data:
            yield k
        if self.defaults is not None:
            for k in self.defaults.propertyNames():
                if k not in self.data:
                    yield k

    def setProperty(self, key, value):
        """ TODO """
        self[key] = value

    def store(self, out, comments=None):
        """ TODO """
        dump(self.data, out, comments=comments)

    def stringPropertyNames(self):
        """ TODO """
        names = set(self.data)
        if self.defaults is not None:
            names.update(self.defaults.stringPropertyNames())
        return names

    def loadFromXML(self, fp):
        """ TODO """
        self.data.update(load_xml(fp))

    def storeToXML(self, out, comment=None, encoding='UTF-8'):
        """ TODO """
        dump_xml(self.data, out, comment=comment, encoding=encoding)

    ###def list(self, out):
    ###    ???
