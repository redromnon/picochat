#!/bin/bash
source venv/bin/activate
pyinstaller --onefile --windowed --name "picochat" main.py --add-data "assets:assets" --icon="assets/picochat_icon.png"