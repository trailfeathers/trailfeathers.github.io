"""
TrailFeathers database module.
Refactored from single database.py into logical submodules.
"""

# Connection utilities
from .connection import get_db_connection, get_cursor

# Users
from .users import (
    get_user_by_id,
    get_user_by_username,
    create_user,
    user_exists_by_username,
    get_first_user,
)

# Trip Reports (Catalog)
from .trip_reports import (
    insert_trip_report_info,
    list_trip_report_info_for_selection,
    get_trip_report_info_by_id,
    get_trip_report_info_for_trip,
)

# Requirements
from .requirements import (
    list_requirement_types,
    list_activity_requirements,
    get_trip_requirement_summary,
)

# Gear
from .gear import (
    add_gear_item,
    list_gear,
    get_gear_item,
    update_gear_item,
    delete_gear_item,
)

# Friends
from .friends import (
    create_friend_request,
    list_incoming_requests,
    accept_friend_request,
    decline_friend_request,
    list_friends,
)

# Favorites
from .favorites import (
    list_favorite_hikes,
    add_favorite_hike,
    remove_favorite_hike,
)

# Profiles
from .profiles import (
    PROFILE_AVATAR_DIR_PREFIX,
    get_user_profile,
    upsert_user_profile,
    set_profile_avatar_upload,
    get_profile_avatar_payload,
)

# Top Four
from .top_four import (
    list_top_four_hikes,
    set_top_four_slot,
    clear_top_four_slot,
    user_has_trip_report_for_info,
    list_top_four_eligible_hikes,
    replace_top_four,
)

# User Trip Reports
from .user_trip_reports import (
    list_user_trip_reports,
    get_user_trip_report,
    set_trip_report_image_upload,
    get_trip_report_image_payload,
    create_user_trip_report,
    update_user_trip_report,
    delete_user_trip_report,
)

# Wishlist
from .wishlist import (
    list_wishlist,
    add_wishlist_item,
    remove_wishlist_item,
)

# Relationships
from .relationships import get_relationship_status, get_relationship, cancel_friend_request, remove_friend

# Trips
from .trips import (
    create_trip,
    get_trip,
    list_trips_for_user,
    update_trip,
    delete_trip,
    user_has_trip_access,
    leave_trip,
    add_trip_collaborator,
)

# Trip Invites
from .trip_invites import (
    invite_user_to_trip,
    create_trip_invite,
    list_trip_invites_pending,
    list_incoming_trip_invites,
    has_pending_invite_to_trip,
    accept_trip_invite,
    decline_trip_invite,
    get_trip_id_for_invite,
    remove_trip_collaborator,
    cancel_trip_invite,
    list_trip_collaborators,
)

# Trip Gear
from .trip_gear import (
    get_trip_gear_pool,
    get_trip_assigned_gear,
    assign_gear_to_trip,
    unassign_gear_from_trip,
)

__all__ = [
    # Connection
    'get_db_connection', 'get_cursor',
    # Users
    'get_user_by_id', 'get_user_by_username', 'create_user', 
    'user_exists_by_username', 'get_first_user',
    # Trip Reports
    'insert_trip_report_info', 'list_trip_report_info_for_selection',
    'get_trip_report_info_by_id', 'get_trip_report_info_for_trip',
    # Requirements
    'list_requirement_types', 'list_activity_requirements',
    'get_trip_requirement_summary',
    # Gear
    'add_gear_item', 'list_gear', 'get_gear_item', 
    'update_gear_item', 'delete_gear_item',
    # Friends
    'create_friend_request', 'list_incoming_requests',
    'accept_friend_request', 'decline_friend_request', 'list_friends',
    # Favorites
    'list_favorite_hikes', 'add_favorite_hike', 'remove_favorite_hike',
    # Profiles
    'PROFILE_AVATAR_DIR_PREFIX', 'get_user_profile', 'upsert_user_profile',
    'set_profile_avatar_upload', 'get_profile_avatar_payload',
    # Top Four
    'list_top_four_hikes', 'set_top_four_slot', 'clear_top_four_slot',
    'user_has_trip_report_for_info', 'list_top_four_eligible_hikes', 'replace_top_four',
    # User Trip Reports
    'list_user_trip_reports', 'get_user_trip_report',
    'set_trip_report_image_upload', 'get_trip_report_image_payload',
    'create_user_trip_report', 'update_user_trip_report', 'delete_user_trip_report',
    # Wishlist
    'list_wishlist', 'add_wishlist_item', 'remove_wishlist_item',
    # Relationships
    'get_relationship_status', 'get_relationship', 'cancel_friend_request', 'remove_friend',
    # Trips
    'create_trip', 'get_trip', 'list_trips_for_user',
    'update_trip', 'delete_trip', 'user_has_trip_access', 'leave_trip', 'add_trip_collaborator',
    # Trip Invites
    'invite_user_to_trip', 'create_trip_invite', 'list_trip_invites_pending',
    'list_incoming_trip_invites', 'has_pending_invite_to_trip',
    'accept_trip_invite', 'decline_trip_invite', 'get_trip_id_for_invite',
    'remove_trip_collaborator', 'cancel_trip_invite', 'list_trip_collaborators',
    # Trip Gear
    'get_trip_gear_pool', 'get_trip_assigned_gear',
    'assign_gear_to_trip', 'unassign_gear_from_trip',
]
