const sqlite3 = require('sqlite3');
const http = require('http');
const db = new sqlite3.Database('stuff.db ');

db.run('CREATE TABLE things (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    n int, x FloatArray(10,9), y FloatArray(10,9)
)');