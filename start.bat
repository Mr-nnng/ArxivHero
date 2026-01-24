@echo off
start "Arxiv Hero Backend" cmd /k "cd /d "%~dp0" && conda activate arxiv && python main.py"
start "Arxiv Hero Frontend" cmd /k "cd /d "%~dp0web_ui\arxiv_hero" && npm run dev"