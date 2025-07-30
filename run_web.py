#!/usr/bin/env python3
"""
Simple entry point to run the AutoGraph web application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from web.flask_app import app

if __name__ == '__main__':
    print("🚀 Starting AutoGraph Web Application...")
    print("📊 Open your browser to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 