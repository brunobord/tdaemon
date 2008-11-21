## Test Daemon


### Installation

Put the tdaemon somewhere where it's executable.

You may run like this:

    $ tdaemon.py --test-program=nose /path/to/python/project

The daemon starts watching the directory and subdirectories. As soon as one file
changes (its content has been changed), the daemon launches the tests
(the `nosetests` program, for example) and you may watch the result.

Two test programs are available:

* nosetests (keyword is `nose`)
* django (keyword is `django`)

When you're using django, the path to the project must be the path where
`manage.py` lives.


