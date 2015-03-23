localkhan
---------

localkhan is a tool to download and distribute
Khan content for offline usage.

Install
```````

.. code:: bash

    $ pip install git+git://github.com/aeby/localkhan.git

Run
```

.. code:: bash

    $ localkhan get --lang=es early-math/cc-early-math-counting-topic
     * Downloading topic structure and 345 media files
    $ localkhan serve
     * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)

Help
````

.. code:: bash

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
