# where is your DB?
grep -n 'path' ../config/example.hyperliquid.toml
# default from store code is spl.db; otherwise [storage].path

# counts + time range
sqlite3 spl.db 'select count(*), min(ts), max(ts) from fills;'

# recent rows
sqlite3 spl.db 'select ts, client_id, side, px, sz, fee from fills order by id desc limit 10;'

# event counts (place/cancel, etc.)
sqlite3 spl.db 'select kind, count(*) from events group by kind;'
sqlite3 spl.db 'select ts, kind, substr(payload,1,120) from events order by id desc limit 10;'
