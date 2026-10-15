# Brazil ETF IOPV Cache

Read-only fallback for public `520870` IOPV quotes. Contains no account,
positions, order interfaces, trading credentials, or private strategy source.

GitHub Actions attempts publication every five minutes on weekdays during
A-share sessions. GitHub scheduling can be delayed; this is not a real-time SLA.
Consumers must check the ORIGINAL upstream `f124` timestamp and `f297` date.
Quotes older than 300 seconds must not create an entry. Publication time never
replaces upstream time. Failed fetches do not refresh an old quote.

Sources: East Money `ulist.np/get` and cross-border ETF `clist/get`, using the
list-quote `f441` IOPV. The unrelated `stock/get` `f441` is NOT used.
Only the matching ETF's four public fields are published.

The same snapshot is published to GitHub Pages at
`https://qaj701224-blip.github.io/brazil-iopv-cache/quote.json` for independent
connectivity validation. Pages deployment adds latency; original quote age
must still be within 300 seconds. A successful publish is not proof that a
JoinQuant runtime can reach either GitHub endpoint.

The default branch is `master`. Run `python -m unittest -q` to validate and
`python publish.py` during a session to fetch a fresh snapshot.
