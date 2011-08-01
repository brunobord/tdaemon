#!/usr/bin/env python
#-*- coding: utf-8 -*-
import tdaemon
import unittest

class Test(unittest.TestCase):

    def test_remove_special_chars(self):
        arguments = r'This is an arguments list + special chars #&;`|*?~<>^()[]{}$\\'
        expected = 'This is an arguments list + special chars '
        self.assertEqual(tdaemon.escapearg(arguments), expected)
