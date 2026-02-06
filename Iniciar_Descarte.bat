@echo off
cd /d "%~dp0"
echo Iniciando Controle de Descarte...
py -m streamlit run app.py
pause