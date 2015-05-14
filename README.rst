.. image:: https://travis-ci.org/aeby/localkhan.svg?branch=master
    :target: https://travis-ci.org/aeby/localkhan
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
      Downloading topics...
      [################################] 1/1 - 00:02:52
      Downloading media assets...
      [###                             ] 50/466 - 00:16:44

    $ localkhan serve
    ****************************************************************
    Visit http://10.10.1.100:5000 on the devices to be synchronized.
    ****************************************************************
    (Press CTRL+C to quit)


Help
````

.. code:: bash

    Usage:
      localkhan get [--base=<path>] [--media-only]  [--lang=<code>] <topic>
      localkhan serve [--base=<path>] [--host=<ipaddr>] [--port=<number>]
      localkhan clean [--base=<path>]
      localkhan -h | --help
      localkhan --version

    Commands:
      get - Download topic structure and media assets
      serve - Serve the content with a simple exercise viewer
      clean -  Clean all downloaded content

    Options:
      --lang=<code>    Language code [default: en].
      --host=<ip>      IP [default: 0.0.0.0].
      --port=<number>  Port number [default: 5000].
      --base=<path>    Download content to this directory [default: ~/.lkhan]
      --media-only     Download only media assets only. Requires a downloaded topic structure.
      -h --help        Show this screen.
      --version        Show version.
