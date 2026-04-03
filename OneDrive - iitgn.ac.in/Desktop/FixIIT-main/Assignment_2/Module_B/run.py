"""
Entry point for running the FixIIT Flask application
Run this file to start the development server
"""
import os

from app import create_app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('APP_PORT', '5000'))
    app.run(host='127.0.0.1', port=port, debug=True)
