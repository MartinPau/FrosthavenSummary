@echo off
echo Starting local web server for Frosthaven Summary...
start http://localhost:8000
python -m http.server 8000
