import datetime as dt
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

BJT = dt.timezone(dt.timedelta(hours=8))
HEADERS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
FIELDS = 'f12,f124,f297,f441'
SOURCES = [
    ('push2delay.eastmoney.com', 'ulist.np/get', {'secids': '1.520870'}),
    ('push2.eastmoney.com', 'ulist.np/get', {'secids': '1.520870'}),
    ('push2.eastmoney.com', 'clist/get', {'fs': 'b:MK0023', 'fid': 'f12',
        'po': '1', 'pz': '100', 'np': '1', 'pn': '1'}),
]


def build_snapshot(payload, now, source):
    if payload.get('rc') != 0:
        raise ValueError('Upstream rejected quote request')
    rows = (payload.get('data') or {}).get('diff') or []
    rows = list(rows.values()) if isinstance(rows, dict) else rows
    row = next((r for r in rows if r.get('f12') == '520870'), None)
    if row is None:
        raise ValueError('Brazil ETF not present')
    value = float(row['f441'])
    stamp = dt.datetime.fromtimestamp(float(row['f124']), dt.timezone.utc).astimezone(BJT)
    age = (now - stamp).total_seconds()
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Invalid IOPV')
    if (stamp.date() != now.date() or str(row.get('f297')) != now.strftime('%Y%m%d')
            or stamp.strftime('%H:%M') < '09:30' or age < -120 or age > 300):
        raise ValueError('Stale, future, or non-session quote')
    copied = {key: row[key] for key in ('f12', 'f124', 'f297', 'f441')}
    return {'rc': 0, 'data': {'diff': [copied]}, 'relay': {
        'schema_version': 1, 'source': source, 'quote_time_bjt': stamp.isoformat(),
        'published_at_bjt': now.isoformat(), 'max_quote_age_seconds': 300}}


def fetch_snapshot():
    errors = []
    for host, endpoint, extra in SOURCES:
        params = dict(extra, fltt='2', invt='2', fields=FIELDS,
                      ut='bd1d9ddb04089700cf9c27f6f7426281')
        for page in range(1, 4 if endpoint == 'clist/get' else 2):
            if endpoint == 'clist/get':
                params['pn'] = str(page)
            url = 'https://%s/api/qt/%s?' % (host, endpoint) + urllib.parse.urlencode(params)
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=5) as response:
                    payload = json.load(response)
                now = dt.datetime.now(dt.timezone.utc).astimezone(BJT)
                try:
                    return build_snapshot(payload, now, host + '/' + endpoint)
                except ValueError as error:
                    total = int((payload.get('data') or {}).get('total') or 0)
                    if str(error) == 'Brazil ETF not present' and page * 100 < total:
                        continue
                    raise
            except Exception as error:
                errors.append('%s/%s: %s' % (host, endpoint, error))
                break
    raise RuntimeError('All IOPV sources failed; old snapshot not refreshed. ' + ' | '.join(errors))


def main():
    now = dt.datetime.now(dt.timezone.utc).astimezone(BJT)
    clock = now.strftime('%H:%M')
    if now.weekday() >= 5 or not ('09:30' <= clock <= '11:30' or '13:00' <= clock <= '15:00'):
        print('Outside A-share session; no publication')
        return
    result = fetch_snapshot()
    serialized = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
    Path('quote.json').write_text(serialized, encoding='utf-8')
    site = Path('_site')
    site.mkdir(exist_ok=True)
    (site / 'quote.json').write_text(serialized, encoding='utf-8')
    row = result['data']['diff'][0]
    print('Published 520870 IOPV=%s upstream_time=%s source=%s' % (
        row['f441'], result['relay']['quote_time_bjt'], result['relay']['source']))


if __name__ == '__main__':
    main()
