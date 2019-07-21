"""Unit tests for Context"""
from tests.utils import NormTestCase


class EvaluationTestCase(NormTestCase):
    def test_with_context(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        results = self.execute("with(tmp), event~'Unix' & tally > 3;")
        self.assertTrue(results is not None)
        self.assertTrue(len(results) > 1)

    def test_foreach_context(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        self.execute("alarms(event:String, ip:String, time:Datetime, tally:Integer);")
        self.execute("alarms := tmp(event?, ip?, time?, tally?);")
        result = self.execute("with(alarms).foreach(event), tally.sum()?total_tally & tally.mean();")
        self.assertTrue(result is not None)
        self.assertTrue(len(result) > 0)
        self.assertTrue('tally.mean' in result.columns)
        self.assertTrue('total_tally' in result.columns)

    def test_foreach_context_multiple_foreach(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        self.execute("alarms(event:String, ip:String, time:Datetime, tally:Integer);")
        self.execute("alarms := tmp(event?, ip?, time?, tally?);")
        result = self.execute("with(alarms).foreach(event, ip), tally.sum()?total_tally & tally.mean();")
        self.assertTrue(result is not None)
        self.assertTrue(len(result) > 0)
        self.assertTrue('tally.mean' in result.columns)
        self.assertTrue('total_tally' in result.columns)

    def test_foreach_context_multiple_foreach_three_agg(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        self.execute("alarms(event:String, ip:String, time:Datetime, tally:Integer);")
        self.execute("alarms := tmp(event?, ip?, time?, tally?);")
        result = self.execute("with(alarms).foreach(event, ip), tally.sum()?total_tally & tally.mean() & tally.count();")
        self.assertTrue(result is not None)
        self.assertTrue(len(result) > 0)
        self.assertTrue('tally.mean' in result.columns)
        self.assertTrue('total_tally' in result.columns)
        self.assertTrue('tally.count' in result.columns)

    def test_foreach_context_multiple_foreach_mixed(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        self.execute("alarms(event:String, ip:String, time:Datetime, tally:Integer);")
        self.execute("alarms := tmp(event?, ip?, time?, tally?);")
        query = """
        with(alarms).foreach(event, ip), tally.sum()?total_tally & tally.mean() & ip~'1.17';
        """
        result = self.execute(query)
        self.assertTrue(result is not None)
        self.assertTrue(len(result) > 0)
        self.assertTrue('tally.mean' in result.columns)
        self.assertTrue('total_tally' in result.columns)
        self.assertTrue(all(result['ip'].str.contains('1.17')))

    def test_foreach_context_multiple_foreach_conditional(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        self.execute("alarms(event:String, ip:String, time:Datetime, tally:Integer);")
        self.execute("alarms := tmp(event?, ip?, time?, tally?);")
        query = """
        with(alarms).foreach(event, ip), tally.sum() > 100;
        """
        result = self.execute(query)
        self.assertTrue(result is not None)
        self.assertTrue(len(result) > 0)
        self.assertTrue('tally.sum' in result.columns)
        self.assertTrue(all(result['tally.sum'] > 100))

    def test_exists_context(self):
        self.execute("tmp := read('./data/norm/packed_alarms.parquet', ext='parq');")
        self.execute("alarms(event:String, ip:String, time:Datetime, tally:Integer);")
        self.execute("alarms := tmp(event?, ip?, time?, tally?);")
        result = self.execute("with(alarms).foreach(event).exist(ip), tally.sum() > 100;")
        self.assertTrue(result is not None)
        self.assertTrue(len(result) > 0)
        self.assertTrue(all(result['tally.sum'] > 100))
        self.assertTrue('ip' in result.columns)
        self.assertTrue(len(result['event'].drop_duplicates()) == len(result))
