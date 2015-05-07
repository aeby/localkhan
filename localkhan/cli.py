# -*- coding: utf-8 -*-
"""Local Khan content.

Usage:
  localkhan get [--lang=<code>] <topic>
  localkhan serve [--host=<ipaddr>] [--port=<number>]
  localkhan -h | --help
  localkhan --version

Options:
  --lang=<code>    Language code [default: en].
  --host=<ip>      IP [default: 0.0.0.0].
  --port=<number>  Port number [default: 5000].
  -h --help        Show this screen.
  --version        Show version.
"""

import sys

from docopt import docopt
from schema import Schema, And, Use, SchemaError, Or

import os
from localkhan import __version__, EX_USAGE, EX_UNAVAILABLE, EX_OK
from localkhan.loader import KhanLoader, KhanLoaderError
from localkhan.serve import app


def main():
    args = docopt(__doc__, version=__version__)
    schema = Schema({
        '--port':
            And(Use(int), lambda n: 0 < n,
                error='--port=<number> should be greater than 0'),
        '--lang':
            And(Use(str), lambda l: len(l) == 2,
                error='--lang=<code> should be a 2 digit country code'),
        '<topic>':
            Or(None, And(Use(str), lambda l: 0 < len(KhanLoader.path_segments(l)) < 4),
               error=('<topic> should contain 1-3 path segments '
                      '(e.g "early-math" or "early-math/cc-early-math-counting-topic/cc-early-math-counting")')
               ),
        str: object  # don't care about other str keys
    })
    try:
        args = schema.validate(args)
    except SchemaError as e:
        print e.message
        return EX_USAGE

    if args['serve']:
        app.run(host=args['--host'], port=args['--port'])
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        loader = KhanLoader(os.path.join(base_dir, 'static/khan'), '/static/khan', language=args['--lang'])
        try:
            return loader.load(args['<topic>'])
        except KhanLoaderError as e:
            print e.message
            return EX_UNAVAILABLE

    return EX_OK


if __name__ == '__main__':
    sys.exit(main())
