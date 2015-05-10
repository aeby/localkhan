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
from __future__ import print_function

import sys
import netifaces
import logging

from docopt import docopt
from schema import Schema, And, Use, SchemaError, Or

import os
from localkhan import __version__, EX_USAGE, EX_UNAVAILABLE, EX_OK
from localkhan.loader import KhanLoader, KhanLoaderError
from localkhan.serve import app


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# We want only IPv4, for now at least
PROTO = netifaces.AF_INET


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
        print(e.message)
        return EX_USAGE

    if args['serve']:
        # Print connect info. Get IP of interface of default gateway if host IP is 0.0.0.0
        host_ip = args['--host']
        if host_ip == '0.0.0.0':
            interface = netifaces.gateways()['default'][PROTO][1]
            for if_address in netifaces.ifaddresses(interface)[PROTO]:
                host_ip = if_address.get('addr', None)

        if host_ip == '0.0.0.0':
            connect_info = "Warning: Unable to determine your external reachable IP address\n" \
                           "Running on http://{0}:{1}".format(host_ip, args['--port'])
        else:
            connect_info = "Visit http://{0}:{1} on the devices to be synchronized.".format(host_ip, args['--port'])

        connect_info_sep = '*' * len(max(connect_info.split('\n')))

        print(connect_info_sep)
        print(connect_info)
        print(connect_info_sep)
        print('\n(Press CTRL+C to quit)')

        app.run(host=args['--host'], port=args['--port'])
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        loader = KhanLoader(os.path.join(base_dir, 'static/khan'), '/static/khan', language=args['--lang'])
        try:
            return loader.load(args['<topic>'])
        except KhanLoaderError as e:
            print(e.message)
            return EX_UNAVAILABLE

    return EX_OK


if __name__ == '__main__':
    sys.exit(main())
