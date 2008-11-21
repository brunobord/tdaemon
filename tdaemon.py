#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import os
from stat import *
import optparse
from time import sleep
import hashlib
import commands
import datetime
import re

IGNORE_EXTENSIONS = ('pyc', 'pyo')

class Watcher(object):
    file_list = {}
    debug = False

    def __init__(self, file_path, test_program, debug=False):
        self.file_path = file_path
        self.file_list = self.walk(file_path)
        self.test_program = test_program
        self.debug = debug

    def include(self, name):
        for extension in IGNORE_EXTENSIONS:
            if name.endswith(extension):
                return False
        return True

    def walk(self, top, file_list={}):
        for root, dirs, files in os.walk(top, topdown=False):
            for name in files:
                if self.include(name):
                    full_path = os.path.join(root, name)
                    file_list[full_path] = hashlib.sha224(open(full_path).read()).hexdigest()
            for name in dirs:
                self.walk(os.path.join(root, name), file_list)
        return file_list

    def diff_list(self, list1, list2):
        for key in list1:
            if key in list2 and list2[key] != list1[key]:
                print key
            elif key not in list2:
                print key

    def run(self, cmd):
        print datetime.datetime.now()
        output = commands.getoutput(cmd)
        print output

    def run_tests(self):
        cmd = None
        if self.test_program == 'nose':
            cmd = "cd %(path)s && nosetests" % {'path': self.file_path}
        elif self.test_program == 'django':
            cmd = "python %s/manage.py test" % self.file_path

        if cmd:
            self.run(cmd)

    def loop(self):
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
        default="nose", help="""specifies the test-program to use. Valid
        values include `nose` and `django`""")
    parser.add_option("-d", "--debug", dest="debug", action="store_true",
        default=False)

    opt, args = parser.parse_args(prog_args)

    if args[1:]:
        path = args[1]
    else:
        path = '.'

    watcher = Watcher(path, opt.test_program, opt.debug)
    watcher.loop()


if __name__ == '__main__':
    main()

