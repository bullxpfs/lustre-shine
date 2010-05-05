#!/usr/bin/env python
# Shine.Configuration.FileSystem class
# Written by A. Degremont 2009-07-17
# $Id$


"""Unit test for Shine.Configuration.FileSystem"""

import sys
import unittest
import tempfile

sys.path.insert(0, '../lib')

from Shine.Configuration.FileSystem import FileSystem
from Shine.Configuration.Exceptions import ConfigInvalidFileSystem

class FileSystemTest(unittest.TestCase):

    def setUp(self):
        self._fs = None

    def tearDown(self):
        if self._fs:
            self._fs.unregister()

    def makeTestFile(self, text):
        """
        Create a temporary file with the provided text.
        """
        tmp = tempfile.NamedTemporaryFile()
        tmp.write(text)
        tmp.flush()
        return tmp

    def makeTestFileSystem(self, text):
        """
        Create a temporary file instance and returns a FileSystem with it.
        """
        testfile = self.makeTestFile(text)
        fsconf = FileSystem(lmf=testfile.name)
        return fsconf

    def testLoadFile(self):
        """create a FileSystem from model example.lmf"""
        self._fs = FileSystem(lmf="../conf/models/example.lmf")
        self.assertEqual(len(self._fs.keys.keys()), 20)

    def testMGSOnly(self):
        """filesystem with only a MGS"""
        self._fs = self.makeTestFileSystem("""
fs_name: example
nid_map: nodes=foo1 nids=foo1@tcp
mgt: node=foo1 dev=/dev/dummy
""")
        self.assertEqual(len(self._fs.keys.keys()), 3)

    def testRouterOnly(self):
        """filesystem with only routers"""
        self._fs = self.makeTestFileSystem("""
fs_name: example
nid_map: nodes=foo1 nids=foo1@tcp
router: node=foo1
""") 
        self.assertEqual(len(self._fs.keys.keys()), 3)

    def testRouterOnly(self):
        """client only filesystem"""
        self._fs = self.makeTestFileSystem("""
fs_name: example
nid_map: nodes=foo[1-3] nids=foo[1-3]@tcp
mgt: node=foo1 dev=/dev/dummy
client: node=foo[2-3]
""") 
        self.assertEqual(len(self._fs.keys.keys()), 4)

    def testMDTnoMGT(self):
        """filesystem with a MDT and no MGT"""
        self.assertRaises(ConfigInvalidFileSystem, self.makeTestFileSystem, """
fs_name: example
nid_map: nodes=foo1 nids=foo1@tcp
mdt: node=foo1 dev=/dev/dummy
""") 

    def testOSTnoMGT(self):
        """filesystem with OSTs and no MGT"""
        self.assertRaises(ConfigInvalidFileSystem, self.makeTestFileSystem, """
fs_name: example
nid_map: nodes=foo[1,2] nids=foo[1,2]@tcp
ost: node=foo1 dev=/dev/dummy
ost: node=foo2 dev=/dev/dummy
""") 

    def testMGTandMDTnoOST(self):
        """filesystem with both MGT and MDT and no OST"""
        self.assertRaises(ConfigInvalidFileSystem, self.makeTestFileSystem, """
fs_name: example
nid_map: nodes=foo1 nids=foo1@tcp
mgt: node=foo1 dev=/dev/dummy2
mdt: node=foo1 dev=/dev/dummy1
""") 


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(FileSystemTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
