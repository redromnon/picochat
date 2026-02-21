#!/bin/bash
source venv/bin/activate
pyinstaller --onefile --windowed --name "picochat" main.py