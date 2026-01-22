@echo off
start "Arxiv Hero Backend" cmd /k "cd /d D:\code\arxiv_hero && conda activate arxiv && python main.py"
start "Arxiv Hero Frontend" cmd /k "cd /d D:\code\arxiv_hero\web_ui\arxiv_hero && npm run dev"