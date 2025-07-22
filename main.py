# This is the main entry point for Replit
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the bot
from python import main

if __name__ == "__main__":
    print("🤖 Starting Anonymous Telegram Bot on Replit...")
    main()
