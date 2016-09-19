from   __future__ import unicode_literals
import re
from   six        import binary_type, StringIO, BytesIO, unichr

def load(fp, object_pairs_hook=dict):
    """
    Parse the contents of the ``.readline``-supporting file-like object ``fp``
    as a ``.properties`` file and return a `dict` of the key-value pairs.

    ``fp`` may be either a text or binary filehandle, with or without universal
    newlines enabled.  If it is a binary filehandle, its contents are decoded
    as Latin-1.

    By default, the key-value pairs extracted from ``fp`` are combined into a
    `dict` with later occurrences of a key overriding previous occurrences of
    the same key.  To change this behavior, pass a callable as the
    ``object_pairs_hook`` argument; it will be called with one argument, a
    generator of ``(key, value)`` pairs representing the key-value entries in
    ``fp`` (including duplicates) in order of occurrence.  `load` will then
    return the value returned by ``object_pairs_hook``.

    :param fp: the file from which to read the ``.properties`` document
    :type fp: file-like object
    :param callable object_pairs_hook: class or function for combining the
        key-value pairs
    :rtype: `dict` or the return value of ``object_pairs_hook``
    """
    return object_pairs_hook(
        (k,v) for k,v,_ in load_items3(fp)
              if k is not None
    )

def loads(s, object_pairs_hook=dict):
    """
    Parse the contents of the string ``s`` as a ``.properties`` file and return
    a `dict` of the key-value pairs.

    ``s`` may be either a text string or bytes string; if it is a bytes string,
    its contents are decoded as Latin-1.

    By default, the key-value pairs extracted from ``s`` are combined into a
    `dict` with later occurrences of a key overriding previous occurrences of
    the same key.  To change this behavior, pass a callable as the
    ``object_pairs_hook`` argument; it will be called with one argument, a
    generator of ``(key, value)`` pairs representing the key-value entries in
    ``s`` (including duplicates) in order of occurrence.  `loads` will then
    return the value returned by ``object_pairs_hook``.

    :param string s: the string from which to read the ``.properties`` document
    :param callable object_pairs_hook: class or function for combining the
        key-value pairs
    :rtype: `dict` or the return value of ``object_pairs_hook``
    """
    if isinstance(s, binary_type):
        fp = BytesIO(s)
    else:
        fp = StringIO(s)
    return load(fp, object_pairs_hook=object_pairs_hook)

def load_items3(fp):
    """ TODO """
    # `fp` may be either a text or binary filehandle, with or without universal
    # newlines support, but it must support the `readline` method.  If `fp` is
    # a binary filehandle, its contents are assumed to be in Latin-1.  If it is
    # a text filehandle, it is assumed to have been opened as Latin-1.
    # Returns an iterator of `(key, value, source_lines)` tuples; blank lines &
    # comments have `key` & `value` values of `None`
    def readline():
        ln = fp.readline()
        if isinstance(ln, binary_type):
            ln = ln.decode('iso-8859-1')
        return ln
    while True:
        line = source = readline()
        if line == '':
            return
        if re.match(r'^[ \t\f]*(?:[#!]|\r?\n?$)', line):
            yield (None, None, source)
            continue
        line = line.lstrip(' \t\f').rstrip('\r\n')
        while re.search(r'(?<!\\)(?:\\\\)*\\$', line):
            line = line[:-1]
            nextline = readline()  # '' at EOF
            source += nextline
            line += nextline.lstrip(' \t\f').rstrip('\r\n')
        if line == '':  # series of otherwise-blank lines with continuations
            yield (None, None, source)
            continue
        m = re.search(r'(?<!\\)(?:\\\\)*([ \t\f]*[=:]|[ \t\f])[ \t\f]*', line)
        if m:
            yield (unescape(line[:m.start(1)]),unescape(line[m.end():]),source)
        else:
            yield (unescape(line), '', source)

_unescapes = {'t': '\t', 'n': '\n', 'f': '\f', 'r': '\r'}

def _unesc(m):
    esc = m.group(1)
    if len(esc) == 1:
        return _unescapes.get(esc, esc)
    else:
        return unichr(int(esc[1:], 16))

def _unsurrogate(m):
    c,d = map(ord, m.group())
    return unichr(((c - 0xD800) << 10) + (d - 0xDC00) + 0x10000)

def unescape(field):
    """
    Decode escape sequences in a ``.properties`` key or value.  The following
    escape sequences are supported::

        \\t \\n \\f \\r \\uXXXX \\\\

    If a backslash is followed by any other character, the backslash is
    dropped.

    In addition, surrogate pairs encoded as two consecutive ``\\uXXXX`` escape
    sequences are decoded into a single character.  (Isolated surrogate code
    points are left as-is.)

    :param field: the string to decode
    :type field: text string
    :rtype: text string
    """
    return re.sub(r'[\uD800-\uDBFF][\uDC00-\uDFFF]', _unsurrogate,
                  re.sub(r'\\(u[0-9A-Fa-f]{4}|.)', _unesc, field))
