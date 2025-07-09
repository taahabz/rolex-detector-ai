import sys
import os

# Add the parent directory to the Python path so we can import from flask_app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app.app import app

# This is the entry point for Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

# For Vercel, we need to expose the app
application = app

if __name__ == "__main__":
    app.run(debug=True) 