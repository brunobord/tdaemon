#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Multi-engine Test Daemon in Python

Original concept by Jeff Winkler in:
http://jeffwinkler.net/nosy-run-python-unit-tests-automatically/

The present code is published under the terms of the MIT License. See LICENSE
file for more details.
"""


import sys
import os
#from stat import *
import optparse
from time import sleep
import hashlib
import commands
import datetime
#import re

IGNORE_EXTENSIONS = ('pyc', 'pyo')
IGNORE_DIRS = ('.bzr', '.git', '.hg', '.darcs', '.svn')
IMPLEMENTED_TEST_PROGRAMS = ('nose', 'nosetests', 'django', 'py')

# -------- Exceptions
class InvalidTestProgram(Exception):
    """Raised as soon as an unexpected test program is chosen"""
    pass

class InvalidFilePath(Exception):
    """Raised if the path to project/module is unknown/missing."""
    pass

class CancelDueToUserRequest(Exception):
    """Raised when user wants to cancel execution"""
    pass

# -------- Utils
def ask(message='Are you sure? [y/N]'):
    """Asks the user his opinion."""
    agree = False
    answer = raw_input(message).lower()
    if answer.startswith('y'):
        agree = True
    return agree

def escapearg(args):
    special_chars = '#&;`|*?~<>^()[]{}$\\'
    print special_chars
    for char in special_chars:
        args = args.replace(char, '')
    return args

class Watcher(object):
    """
    Watcher class. This is the daemon that is watching every file in the
    directory and subdirectories, and that runs the test process.
    """
    file_list = {}
    debug = False

    def __init__(self, file_path, test_program, debug=False, custom_args=''):
        # Safe filter
        custom_args = escapearg(custom_args)

        # check configuration
        self.check_configuration(file_path, test_program, custom_args)

        self.file_path = file_path
        self.file_list = self.walk(file_path)
        self.test_program = test_program
        self.custom_args = custom_args

        self.check_dependencies()
        self.debug = debug
        self.cmd = self.get_cmd()


    def check_configuration(self, file_path, test_program, custom_args):
        """Checks if configuration is ok."""
        # checking filepath
        if not os.path.isdir(file_path):
            raise InvalidFilePath("INVALID CONFIGURATION: "
            "file path %s is not a directory" %
                os.path.abspath(file_path)
            )

        if not test_program in IMPLEMENTED_TEST_PROGRAMS:
            raise InvalidTestProgram('The `%s` is unknown, or not yet '
            'implemented. Please chose another one.' % test_program)

        if custom_args:
            if not ask("WARNING!!!\nYou are about to run the following command\n\n   $ %s %s\n\nAre you sure you still want to proceed [y/N]? " % (test_program, custom_args)):
                raise CancelDueToUserRequest('Test cancelled...')

    def check_dependencies(self):
        "Checks if the test program is available in the python environnement"
        if self.test_program == 'nose':
            try:
                import nose
            except ImportError:
                sys.exit('Nosetests is not available on your system.'
                ' Please install it and try to run it again')

    def get_cmd(self):
        cmd = None
        if self.test_program in ('nose', 'nosetests'):
            cmd = "cd %s && nosetests" % self.file_path
        elif self.test_program == 'django':
            cmd = "python %s/manage.py test" % self.file_path
        elif self.test_program == 'py':
            cmd = 'py.test %s' % self.file_path

        if not cmd:
            raise InvalidTestProgram("The test program %s is unknown."
                "Valid options are `nose` and `django`" % self.test_program)

        # adding custom args
        if self.custom_args:
            cmd = '%s %s' % (cmd, self.custom_args)
        return cmd

    # Path manipulation
    def include(self, path):
        """Returns `True` if the file is not ignored"""
        for extension in IGNORE_EXTENSIONS:
            if path.endswith(extension):
                return False
        parts = path.split(os.path.sep)
        for part in parts:
            if part in IGNORE_DIRS:
                return False
        return True

    def walk(self, top, file_list={}):
        """Walks the walk. nah, seriously: reads the file and stores a hashkey
        corresponding to its content."""
        for root, dirs, files in os.walk(top, topdown=False):
            if os.path.basename(root) in IGNORE_DIRS:
                # Do not dig in ignored dirs
                continue

            for name in files:
                full_path = os.path.join(root, name)
                if self.include(full_path):
                    if os.path.isfile(full_path):
                        # preventing fail if the file vanishes
                        content = open(full_path).read()
                        hashcode = hashlib.sha224(content).hexdigest()
                        file_list[full_path] = hashcode
            for name in dirs:
                if name not in IGNORE_DIRS:
                    self.walk(os.path.join(root, name), file_list)
        return file_list

    def file_sizes(self):
        """Returns total filesize (in MB)"""
        size = sum(map(os.path.getsize, self.file_list))
        return size / 1024 / 1024


    def diff_list(self, list1, list2):
        """Extracts differences between lists. For debug purposes"""
        for key in list1:
            if key in list2 and list2[key] != list1[key]:
                print key
            elif key not in list2:
                print key

    def run(self, cmd):
        """Runs the appropriate command"""
        print datetime.datetime.now()
        output = commands.getoutput(cmd)
        print output

    def run_tests(self):
        """Execute tests"""
        self.run(self.cmd)

    def loop(self):
        """Main loop daemon."""
        while True:
            sleep(1)
            new_file_list = self.walk(self.file_path, {})
            if new_file_list != self.file_list:
                if self.debug:
                    self.diff_list(new_file_list, self.file_list)
                self.run_tests()
                self.file_list = new_file_list

def main(prog_args=None):
    """
    What do you expect?
    """
    if prog_args is None:
        prog_args = sys.argv

    parser = optparse.OptionParser()
    parser.usage = """Usage: %[prog] [options] [<path>]"""
    parser.add_option("-t", "--test-program", dest="test_program",
        default="nose", help="specifies the test-program to use. Valid values"
        " include `nose` (or `nosetests`), `django` and `py` (for `py.test`)")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        default=False)
    parser.add_option('-s', '--size-max', dest='size_max', default=25,
        type="int", help="Sets the maximum size (in MB) of files.")
    parser.add_option('--custom-args', dest='custom_args', default='',
        type="str",
        help="Defines custom arguments to pass after the test program command")

    opt, args = parser.parse_args(prog_args)

    if args[1:]:
        path = args[1]
    else:
        path = '.'

    try:
        watcher = Watcher(path, opt.test_program, opt.debug, opt.custom_args)
        watcher_file_size = watcher.file_sizes()
        if watcher_file_size > opt.size_max:
            message =  "It looks like the total file size (%dMb) is larger " \
                "than the  `max size` option (%dMb)." \
                "\nThis may slow down the file comparison process, and thus " \
                "the daemon performance." \
                "\nDo you wish to continue? [y/N] " % (watcher_file_size, opt.size_max)

            if not ask(message):
                raise CancelDueToUserRequest('Ok, thx, bye...')

        print "Ready to watch file changes..."
        watcher.loop()
    except Exception, e:
        print e

    print "Bye"

if __name__ == '__main__':
    main()

