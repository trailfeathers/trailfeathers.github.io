"""
TrailFeathers - Health check: GET / returns "OK" for load balancers and uptime checks.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
def register(app):
    """Register health route (no auth)."""
    @app.get("/")
    def health():
        return "OK"

