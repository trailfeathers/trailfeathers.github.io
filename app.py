"""
TrailFeathers - WSGI entry point; creates the Flask app via tf_server.create_app (e.g. for Gunicorn).
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
import os

from tf_server import create_app

# Gunicorn entry point
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
