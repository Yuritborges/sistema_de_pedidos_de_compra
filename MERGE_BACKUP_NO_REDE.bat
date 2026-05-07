@echo off
setlocal
set "BASE=%~dp0"
set "PY=%BASE%.venv\Scripts\python.exe"
set "SCRIPT=%BASE%tools\merge_backup_diario_into_rede.py"
if not exist "%PY%" set "PY=python"
if not exist "%SCRIPT%" (
  echo Script nao encontrado: "%SCRIPT%"
  exit /b 1
)
echo Mesclando backup diario Iury+Thamyres no cotacao_rede.db...
"%PY%" "%SCRIPT%" %*
exit /b %ERRORLEVEL%
