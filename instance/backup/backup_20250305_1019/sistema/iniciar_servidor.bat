@echo off
echo Iniciando o sistema de backup automatico...
start /B python backup_system.py

echo Iniciando o servidor...
echo O sistema estara disponivel em http://10.0.0.222:5000
python app.py
pause
