"""
TrailFeathers - Database module; re-exports all public API from domain submodules.
Group: TrailFeathers
Authors: Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor, get_db_connection
from .users import (
    create_user,
    get_first_user,
    get_user_by_id,
    get_user_by_username,
    user_exists_by_username,
)
from .trip_report_info import (
    get_trip_report_info_by_id,
    get_trip_report_info_for_trip,
    insert_trip_report_info,
    list_trip_report_info_for_selection,
)
from .requirements import (
    get_trip_requirement_summary,
    list_activity_requirements,
    list_requirement_types,
)
from .gear import (
    add_gear_item,
    delete_gear_item,
    get_gear_item,
    list_gear,
    update_gear_item,
)
from .friends import (
    accept_friend_request,
    cancel_friend_request,
    create_friend_request,
    decline_friend_request,
    get_relationship,
    list_friends,
    list_incoming_requests,
    remove_friend,
)
from .favorites import (
    add_favorite_hike,
    list_favorite_hikes,
    remove_favorite_hike,
)
from .profiles import (
    PROFILE_AVATAR_DIR_PREFIX,
    get_profile_avatar_payload,
    get_user_profile,
    set_profile_avatar_upload,
    upsert_user_profile,
)
from .top_four import (
    clear_top_four_slot,
    list_top_four_eligible_hikes,
    list_top_four_hikes,
    replace_top_four,
    set_top_four_slot,
    user_has_trip_report_for_info,
)
from .user_trip_reports import (
    create_user_trip_report,
    delete_user_trip_report,
    get_trip_report_image_payload,
    get_user_trip_report,
    list_user_trip_reports,
    set_trip_report_image_upload,
    update_user_trip_report,
)
from .wishlist import (
    add_wishlist_item,
    list_wishlist,
    remove_wishlist_item,
)
from .trips import (
    ACTIVITY_TYPES,
    add_trip_collaborator,
    create_trip,
    delete_trip,
    get_trip,
    leave_trip,
    list_trip_collaborators,
    list_trips_for_user,
    remove_trip_collaborator,
    update_trip,
    user_has_trip_access,
)
from .trip_invites import (
    accept_trip_invite,
    cancel_trip_invite,
    create_trip_invite,
    decline_trip_invite,
    get_trip_id_for_invite,
    has_pending_invite_to_trip,
    list_incoming_trip_invites,
    list_trip_invites_pending,
)
from .trip_gear import (
    assign_gear_to_trip,
    get_trip_assigned_gear,
    get_trip_gear_pool,
    unassign_gear_from_trip,
)

__all__ = [
    "get_cursor",
    "get_db_connection",
    "create_user",
    "get_first_user",
    "get_user_by_id",
    "get_user_by_username",
    "user_exists_by_username",
    "get_trip_report_info_by_id",
    "get_trip_report_info_for_trip",
    "insert_trip_report_info",
    "list_trip_report_info_for_selection",
    "get_trip_requirement_summary",
    "list_activity_requirements",
    "list_requirement_types",
    "add_gear_item",
    "delete_gear_item",
    "get_gear_item",
    "list_gear",
    "update_gear_item",
    "accept_friend_request",
    "cancel_friend_request",
    "create_friend_request",
    "decline_friend_request",
    "get_relationship",
    "list_friends",
    "list_incoming_requests",
    "remove_friend",
    "add_favorite_hike",
    "list_favorite_hikes",
    "remove_favorite_hike",
    "PROFILE_AVATAR_DIR_PREFIX",
    "get_profile_avatar_payload",
    "get_user_profile",
    "set_profile_avatar_upload",
    "upsert_user_profile",
    "clear_top_four_slot",
    "list_top_four_eligible_hikes",
    "list_top_four_hikes",
    "replace_top_four",
    "set_top_four_slot",
    "user_has_trip_report_for_info",
    "create_user_trip_report",
    "delete_user_trip_report",
    "get_trip_report_image_payload",
    "get_user_trip_report",
    "list_user_trip_reports",
    "set_trip_report_image_upload",
    "update_user_trip_report",
    "add_wishlist_item",
    "list_wishlist",
    "remove_wishlist_item",
    "ACTIVITY_TYPES",
    "add_trip_collaborator",
    "create_trip",
    "delete_trip",
    "get_trip",
    "leave_trip",
    "list_trip_collaborators",
    "list_trips_for_user",
    "remove_trip_collaborator",
    "update_trip",
    "user_has_trip_access",
    "accept_trip_invite",
    "cancel_trip_invite",
    "create_trip_invite",
    "decline_trip_invite",
    "get_trip_id_for_invite",
    "has_pending_invite_to_trip",
    "list_incoming_trip_invites",
    "list_trip_invites_pending",
    "assign_gear_to_trip",
    "get_trip_assigned_gear",
    "get_trip_gear_pool",
    "unassign_gear_from_trip",
]
