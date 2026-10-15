import datetime as dt
import unittest

from publish import build_snapshot

NOW = dt.datetime(2026, 10, 15, 10, 28, tzinfo=dt.timezone(dt.timedelta(hours=8)))


def payload(age=0, value=1.3037, day='20261015', code='520870'):
    stamp = (NOW - dt.timedelta(seconds=age)).timestamp()
    return {'rc': 0, 'data': {'diff': [{'f12': code, 'f441': value, 'f124': stamp, 'f297': day}]}}


class PublishTests(unittest.TestCase):
    def test_exact_upstream_timestamp_and_value_are_preserved(self):
        data = payload(age=15)
        result = build_snapshot(data, NOW, 'push2.eastmoney.com/clist/get')
        self.assertEqual(result['data']['diff'], data['data']['diff'])
        self.assertEqual(result['data']['diff'][0]['f441'], 1.3037)

    def test_rejects_stale_future_wrong_date_and_wrong_code(self):
        for kwargs in ({'age': 301}, {'age': -121}, {'day': '20261014'}, {'code': '513350'},
                       {'value': 0}, {'value': float('nan')}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                build_snapshot(payload(**kwargs), NOW, 'source')

    def test_dict_rows_are_supported(self):
        data = payload()
        data['data']['diff'] = {'0': data['data']['diff'][0]}
        self.assertEqual(build_snapshot(data, NOW, 'source')['data']['diff'][0]['f12'], '520870')


if __name__ == '__main__':
    unittest.main()
