"""Unit tests for Norm"""
from tests.utils import NormTestCase


class VersioningTestCase(NormTestCase):

    def test_same_version_for_draft(self):
        lam = self.execute("version_test(test:Integer);")
        script = """
        // revising leads to a different version
        version_test(test:Integer, test2:String);
        """
        lam2 = self.execute(script)
        self.assertTrue(lam2.version != lam.version)

    def test_version_up(self):
        self.execute("version_test(test:Integer);")
        lam1 = self.execute("export version_test;")
        self.execute("version_test(test:Integer, test2:String);")
        lam2 = self.execute("export version_test;")
        self.assertTrue(lam2.version != lam1.version and lam2.created_on > lam1.created_on)

