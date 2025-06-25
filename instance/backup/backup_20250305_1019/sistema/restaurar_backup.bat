@echo off
echo Restaurando backup %1 (Tipo: %2)...

REM Encerrar o servidor Flask
taskkill /F /IM python.exe

REM Aguardar um momento
timeout /t 5

REM Executar script de restauração
python restore_backup.py %1 %2

REM Aguardar um momento
timeout /t 3

REM Reiniciar o servidor
start /B iniciar_servidor.bat

echo Processo de restauração concluído!
