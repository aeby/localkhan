# -*- coding: utf-8 -*-
"""Local Khan content.

Usage:
  localkhan get [--lang=<code>] <topic>
  localkhan serve [--host=<ipaddr>] [--port=<number>]
  localkhan -h | --help
  localkhan --version

Options:
  -h --help        Show this screen.
  --version        Show version.
  --lang=<code>    Language code [default: en].
  --host=<ip>      IP [default: 0.0.0.0].
  --port=<number>  Port number [default: 5000].

"""

from docopt import docopt
from schema import Schema, And, Or, Use, SchemaError

from . import __version__
from .serve import app


def main():
    args = docopt(__doc__, version=__version__)
    schema = Schema(Or(None, And(Use(int), lambda n: 0 < n),
                       error='--port=<number> should be greater than 0'))
    try:
        # todo(aeby): validate host IP
        args['--port'] = schema.validate(args['--port'])
    except SchemaError as e:
        exit(e)

    if args['serve']:
        app.run(host=args['--host'], port=args['--port'])
    else:
        print(' * Get %s' % args['<topic>'])


if __name__ == '__main__':
    main()
