from   __future__ import print_function, unicode_literals
import argparse
import re
import sys
from   six        import PY2, iteritems
from   .reading   import load, parse, unescape
from   .writing   import dump, join_key_value, java_timestamp, to_comment
from   .util      import properties_reader, properties_writer, propout, propin

def main():
    argstr = (lambda s: s.decode(sys.getfilesystemencoding())) if PY2 else str
    parser = argparse.ArgumentParser()
    cmds = parser.add_subparsers(title='command', dest='cmd')

    cmd_get = cmds.add_parser('get')
    cmd_get.add_argument('-d', '--default-value', metavar='VALUE')
    cmd_get.add_argument('-D', '--defaults', metavar='FILE',
                         type=properties_reader)
    cmd_get.add_argument('-e', '--escaped', action='store_true')
    cmd_get.add_argument('-P', '--properties', action='store_true')
    cmd_get.add_argument('-s', '--separator', default='=')
    cmd_get.add_argument('file', type=properties_reader)
    cmd_get.add_argument('key', nargs='+', type=argstr)

    cmd_set = cmds.add_parser('set')
    cmd_set.add_argument('-e', '--escaped', action='store_true')
    cmd_set.add_argument('-o', '--outfile', type=properties_writer,
                         default=propout)
    cmd_set.add_argument('-s', '--separator', default='=')
    cmd_set.add_argument('-T', '--preserve-timestamp', action='store_true')
    cmd_set.add_argument('file', type=properties_reader)
    cmd_set.add_argument('key', type=argstr)
    cmd_set.add_argument('value', type=argstr)

    cmd_del = cmds.add_parser('delete')
    cmd_del.add_argument('-e', '--escaped', action='store_true')
    cmd_del.add_argument('-o', '--outfile', type=properties_writer,
                         default=propout)
    cmd_del.add_argument('-T', '--preserve-timestamp', action='store_true')
    cmd_del.add_argument('file', type=properties_reader)
    cmd_del.add_argument('key', nargs='+', type=argstr)

    cmd_format = cmds.add_parser('format')
    cmd_format.add_argument('-o', '--outfile', type=properties_writer,
                            default=propout)
    cmd_format.add_argument('-s', '--separator', default='=')
    cmd_format.add_argument('file', type=properties_reader, default=propin)

    args = parser.parse_args()

    if args.cmd == 'get':
        ok = True
        if args.escaped:
            args.key = list(map(unescape, args.key))
        props = getproperties(args.file, args.key)
        if args.defaults is not None:
            defaults = getproperties(args.defaults, args.key)
        else:
            defaults = {}
        for k in args.key:
            v = args.default_value
            if k in props:
                v = props[k]
            elif k in defaults:
                v = defaults[k]
            if v is None:
                print('javaproperties: {0!r}: key not found'.format(k),
                      file=sys.stderr)
                ok = False
            elif args.properties:
                print(join_key_value(k, v, separator=args.separator))
            else:
                print(v)
        sys.exit(0 if ok else 1)

    elif args.cmd == 'set':
        if args.escaped:
            args.key = unescape(args.key)
            args.value = unescape(args.value)
        setproperties(args.file, args.outfile, {args.key: args.value},
                      args.preserve_timestamp, args.separator)

    elif args.cmd == 'delete':
        if args.escaped:
            args.key = list(map(unescape, args.key))
        setproperties(args.file, args.outfile, dict.fromkeys(args.key),
                      args.preserve_timestamp, args.separator)

    elif args.cmd == 'format':
        dump(load(args.file), args.outfile, sort_keys=True,
             separator=args.separator)

    else:
        assert False, 'No path defined for command {0!r}'.format(args.cmd)


def getproperties(fp, keys):
    keys = set(keys)
    def getprops(seq):
        props = {}
        for k,v in seq:
            if k in keys:
                props[k] = v
        return props
    return load(fp, object_pairs_hook=getprops)

TIMESTAMP_RGX = r'^\s*[#!]\s*\w+ \w+ [ \d]?\d \d\d:\d\d:\d\d \w* \d{4,}\s*$'

def setproperties(fpin, fpout, newprops, preserve_timestamp=False,
                  separator='='):
    in_header = True
    prevsrc = None
    for k, _, src in parse(fpin):
        if in_header:
            if k is None:
                if prevsrc is not None:
                    print(prevsrc, end='', file=fpout)
                prevsrc = src
                continue
            else:
                if prevsrc is not None:
                    if preserve_timestamp:
                        print(prevsrc, end='', file=fpout)
                    else:
                        if not re.match(TIMESTAMP_RGX, prevsrc, flags=re.U):
                            print(prevsrc, end='', file=fpout)
                        print(to_comment(java_timestamp()), file=fpout)
                elif not preserve_timestamp:
                    print(to_comment(java_timestamp()), file=fpout)
                in_header = False
        if k in newprops:
            if newprops[k] is not None:
                print(join_key_value(k, newprops[k], separator=separator),
                      file=fpout)
                newprops[k] = None
        else:
            print(src, end='', file=fpout)
    for key, value in iteritems(newprops):
        if value is not None:
            print(join_key_value(key, value, separator=separator), file=fpout)

if __name__ == '__main__':
    main()
