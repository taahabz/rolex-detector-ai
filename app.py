import os
import sys

# Add the flask_app directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
flask_app_dir = os.path.join(current_dir, 'flask_app')
sys.path.insert(0, flask_app_dir)

# Import the Flask app from the flask_app directory
from flask_app.app import app

# Configure for Heroku deployment
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False) 