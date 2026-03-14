"""
Health check. Single route: GET / returns "OK" for load balancers and uptime checks.
"""
def register(app):
    """Register health route (no auth)."""
    @app.get("/")
    def health():
        return "OK"

