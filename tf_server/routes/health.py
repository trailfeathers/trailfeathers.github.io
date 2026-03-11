def register(app):
    # ----------------------
    # Health check
    # ----------------------
    @app.get("/")
    def health():
        return "OK"

