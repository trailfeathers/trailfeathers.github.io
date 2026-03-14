"""
TrailFeathers - CORS preflight OPTIONS handlers for all API routes (return 200); no auth.
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
def register(app):
    """Register OPTIONS handlers for CORS preflight (return 200)."""
    @app.route("/api/signup", methods=["OPTIONS"])
    @app.route("/api/login", methods=["OPTIONS"])
    @app.route("/api/gear", methods=["OPTIONS"])
    @app.route("/api/gear/<int:gear_id>", methods=["OPTIONS"])
    @app.route("/api/friends/request", methods=["OPTIONS"])
    @app.route("/api/friends/requests", methods=["OPTIONS"])
    @app.route("/api/friends", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>/accept", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>/decline", methods=["OPTIONS"])
    @app.route("/api/trips", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/checklist", methods=["OPTIONS"])
    @app.route("/api/requirement-types", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/collaborators", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/collaborators/<int:user_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/invites", methods=["OPTIONS"])
    @app.route("/api/trip-invites", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>/accept", methods=["OPTIONS"])
    @app.route("/api/trip-invites/<int:invite_id>/decline", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear/pool", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/gear/<int:gear_id>", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/dashboard", methods=["OPTIONS"])
    @app.route("/api/trips/<int:trip_id>/weather", methods=["OPTIONS"])
    @app.route("/api/locations", methods=["OPTIONS"])
    @app.route("/api/me/favorites", methods=["OPTIONS"])
    @app.route("/api/me/favorites/<int:trip_report_info_id>", methods=["OPTIONS"])
    @app.route("/api/me/profile", methods=["OPTIONS"])
    @app.route("/api/profile-avatars", methods=["OPTIONS"])
    @app.route("/api/me/profile/avatar", methods=["OPTIONS"])
    @app.route("/api/me/avatar", methods=["OPTIONS"])
    @app.route("/api/users/<path:username>/avatar", methods=["OPTIONS"])
    @app.route("/api/me/top-four", methods=["OPTIONS"])
    @app.route("/api/me/top-four-eligible", methods=["OPTIONS"])
    @app.route("/api/me/trip-reports", methods=["OPTIONS"])
    @app.route("/api/me/trip-reports/<int:report_id>", methods=["OPTIONS"])
    @app.route("/api/me/trip-reports/<int:report_id>/image", methods=["OPTIONS"])
    @app.route("/api/trip-reports/<int:report_id>", methods=["OPTIONS"])
    @app.route("/api/trip-reports/<int:report_id>/image", methods=["OPTIONS"])
    @app.route("/api/me/wishlist", methods=["OPTIONS"])
    @app.route("/api/me/wishlist/<int:trip_report_info_id>", methods=["OPTIONS"])
    @app.route("/api/users/<path:username>", methods=["OPTIONS"])
    @app.route("/api/friends/<int:friend_user_id>", methods=["OPTIONS"])
    @app.route("/api/friends/requests/<int:request_id>", methods=["OPTIONS"])
    def options_auth(
        request_id=None,
        trip_id=None,
        invite_id=None,
        gear_id=None,
        trip_report_info_id=None,
        user_id=None,
        report_id=None,
        username=None,
        friend_user_id=None,
    ):
        return "", 200

