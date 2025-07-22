#!/usr/bin/env bash
# Build script for Telegram Bot on Render

echo "Installing Python dependencies for Telegram Bot..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed successfully!"
