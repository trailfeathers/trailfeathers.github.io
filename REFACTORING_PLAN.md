# TrailFeathers Codebase Refactoring Plan

**Created**: 2026-02-12
**Status**: Planning Phase
**Risk Level**: Medium - Requires careful testing after each module

---

## Overview

This document provides a detailed plan for splitting three large files into modular components:

- `database/database.py` (1,455 lines) → `db/` module
- `static/script.js` (1,754 lines) → `static/js/` modules
- `static/styles.css` (1,470 lines) → `static/css/` modules

**Total Lines to Refactor**: ~3,700

---

## Part 1: Database Module Split

### Current Structure
```
database/
  └── database.py (1,455 lines)
```

### Target Structure
```
db/
  ├── __init__.py          # Exports all functions
  ├── connection.py        # Database connection utilities
  ├── users.py            # User management (lines 50-91)
  ├── trip_reports.py     # Trip report catalog (lines 93-185)
  ├── requirements.py     # Activity requirements (lines 186-298)
  ├── gear.py             # Gear/inventory (lines 299-460)
  ├── friends.py          # Friends management (lines 461-540)
  ├── favorites.py        # Favorite hikes (lines 541-588)
  ├── profiles.py         # User profiles (lines 589-688)
  ├── top_four.py         # Top four hikes feature (lines 689-822)
  ├── user_trip_reports.py # User-created trip reports (lines 823-958)
  ├── wishlist.py         # Wishlist feature (lines 959-996)
  ├── relationships.py    # User relationships (lines 997-1043)
  ├── trips.py            # Trip management (lines 1044-1237)
  ├── trip_invites.py     # Trip invitations (lines 1238-1382)
  └── trip_gear.py        # Trip equipment assignment (lines 1383-1455)
```

### Step-by-Step Implementation

#### Step 1: Create `db/connection.py`
```python
"""
Database connection utilities for TrailFeathers.
Uses DATABASE_URL (e.g. Neon PostgreSQL).
"""
import os
from contextmanager import contextmanager

# Prefer psycopg2 for RealDictCursor; fall back to psycopg (v3)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    _use_psycopg2 = True
except ImportError:
    import psycopg
    _use_psycopg2 = False


def get_db_connection():
    """Return a live DB connection (cursor returns dict-like rows)."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    if _use_psycopg2:
        return psycopg2.connect(url, cursor_factory=RealDictCursor)
    conn = psycopg.connect(url)
    conn.row_factory = psycopg.rows.dict_row
    return conn


@contextmanager
def get_cursor():
    """Context manager: connection + cursor that returns dict rows."""
    conn = get_db_connection()
    try:
        if _use_psycopg2:
            cur = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()
```

#### Step 2: Create `db/users.py`
```python
"""User management functions."""
from .connection import get_cursor


def get_user_by_id(user_id):
    # Copy lines 51-54 from database.py
    pass


def get_user_by_username(username):
    # Copy lines 57-63 from database.py
    pass


def create_user(username, password_hash):
    # Copy lines 66-72 from database.py
    pass


def user_exists_by_username(username):
    # Copy lines 75-78 from database.py
    pass


def get_first_user():
    # Copy lines 81-90 from database.py
    pass
```

#### Step 3: Create `db/trip_reports.py`
```python
"""Trip report catalog functions."""
from .connection import get_cursor


def insert_trip_report_info(trip_id, info):
    # Copy lines 93-144 from database.py
    pass


def list_trip_report_info_for_selection():
    # Copy lines 147-156 from database.py
    pass


def get_trip_report_info_by_id(info_id):
    # Copy lines 159-168 from database.py
    pass


def get_trip_report_info_for_trip(trip_id):
    # Copy lines 171-183 from database.py
    pass
```

#### Step 4: Create `db/requirements.py`
```python
"""Activity requirements and gear requirement types."""
from .connection import get_cursor


def list_requirement_types():
    # Copy lines 187-194 from database.py
    pass


def list_activity_requirements(activity_type):
    # Copy lines 197-211 from database.py
    pass


def _required_count_for_rule(rule, quantity, n_persons, num_people):
    # Copy lines 213-223 from database.py
    pass


def _covered_count_for_type(assigned_gear_rows):
    # Copy lines 225-237 from database.py
    pass


def get_trip_requirement_summary(trip_id):
    # Copy lines 239-298 from database.py
    # NOTE: This imports from trips module, handle circular dependency
    pass
```

#### Step 5: Create `db/gear.py`
```python
"""Gear/inventory management functions."""
from .connection import get_cursor


def add_gear_item(user_id, payload):
    # Copy lines 300-346 from database.py
    pass


def list_gear(user_id):
    # Copy lines 347-361 from database.py
    pass


def get_gear_item(gear_id, user_id):
    # Copy lines 362-376 from database.py
    pass


def _parse_gear_payload(payload):
    # Copy lines 377-425 from database.py
    pass


def update_gear_item(gear_id, user_id, payload):
    # Copy lines 426-451 from database.py
    pass


def delete_gear_item(gear_id, user_id):
    # Copy lines 452-460 from database.py
    pass
```

#### Step 6: Create `db/friends.py`
```python
"""Friends and social features."""
from .connection import get_cursor


def create_friend_request(sender_id, receiver_id):
    # Copy lines 462-489 from database.py
    pass


def list_incoming_requests(receiver_id):
    # Copy lines 490-503 from database.py
    pass


def accept_friend_request(request_id, receiver_id):
    # Copy lines 504-514 from database.py
    pass


def decline_friend_request(request_id, receiver_id):
    # Copy lines 515-525 from database.py
    pass


def list_friends(user_id):
    # Copy lines 526-540 from database.py
    pass
```

#### Step 7: Create `db/favorites.py`
```python
"""User favorite hikes from catalog."""
from .connection import get_cursor


def list_favorite_hikes(user_id):
    # Copy lines 544-557 from database.py
    pass


def add_favorite_hike(user_id, trip_report_info_id):
    # Copy lines 558-578 from database.py
    pass


def remove_favorite_hike(user_id, trip_report_info_id):
    # Copy lines 579-588 from database.py
    pass
```

#### Step 8: Create `db/profiles.py`
```python
"""User profile management."""
from .connection import get_cursor, get_db_connection


def get_user_profile(user_id):
    # Copy lines 594-608 from database.py
    pass


def upsert_user_profile(user_id, display_name=None, bio=None, avatar_path=None):
    # Copy lines 609-651 from database.py
    pass


def set_profile_avatar_upload(user_id, image_bytes, media_type):
    # Copy lines 652-671 from database.py
    pass


def get_profile_avatar_payload(user_id):
    # Copy lines 672-688 from database.py
    pass
```

#### Step 9: Create `db/top_four.py`
```python
"""Top four hikes feature for user profiles."""
from .connection import get_cursor


def list_top_four_hikes(user_id):
    # Copy lines 690-730 from database.py
    pass


def set_top_four_slot(user_id, position, trip_report_info_id):
    # Copy lines 731-750 from database.py
    pass


def clear_top_four_slot(user_id, position):
    # Copy lines 751-761 from database.py
    pass


def user_has_trip_report_for_info(user_id, trip_report_info_id):
    # Copy lines 762-777 from database.py
    pass


def list_top_four_eligible_hikes(user_id):
    # Copy lines 778-791 from database.py
    pass


def replace_top_four(user_id, slots):
    # Copy lines 792-822 from database.py
    pass
```

#### Step 10: Create `db/user_trip_reports.py`
```python
"""User-created trip reports."""
from .connection import get_cursor, get_db_connection


def list_user_trip_reports(user_id):
    # Copy lines 824-838 from database.py
    pass


def get_user_trip_report(report_id, user_id=None):
    # Copy lines 839-864 from database.py
    pass


def set_trip_report_image_upload(report_id, user_id, image_bytes, media_type):
    # Copy lines 865-882 from database.py
    pass


def get_trip_report_image_payload(report_id):
    # Copy lines 883-895 from database.py
    pass


def create_user_trip_report(user_id, trip_report_info_id, title, body="", date_hiked=None):
    # Copy lines 896-913 from database.py
    pass


def update_user_trip_report(report_id, user_id, trip_report_info_id=None, title=None, body=None, date_hiked=None):
    # Copy lines 914-949 from database.py
    pass


def delete_user_trip_report(report_id, user_id):
    # Copy lines 950-958 from database.py
    pass
```

#### Step 11: Create `db/wishlist.py`
```python
"""Wishlist feature for hikes."""
from .connection import get_cursor


def list_wishlist(user_id):
    # Copy lines 960-973 from database.py
    pass


def add_wishlist_item(user_id, trip_report_info_id):
    # Copy lines 974-987 from database.py
    pass


def remove_wishlist_item(user_id, trip_report_info_id):
    # Copy lines 988-996 from database.py
    pass
```

#### Step 12: Create `db/relationships.py`
```python
"""User relationship management."""
from .connection import get_cursor


def get_relationship_status(user_id, other_user_id):
    # Copy lines 997-1043 from database.py
    pass
```

#### Step 13: Create `db/trips.py`
```python
"""Trip management functions."""
from .connection import get_cursor


def create_trip(creator_id, payload):
    # Copy lines 1044-1080 from database.py
    pass


def get_trip(trip_id):
    # Copy lines 1081-1099 from database.py
    pass


def list_trips_for_user(user_id):
    # Copy lines 1100-1120 from database.py
    pass


def update_trip(trip_id, user_id, payload):
    # Copy lines 1121-1166 from database.py
    pass


def delete_trip(trip_id, user_id):
    # Copy lines 1167-1189 from database.py
    pass


def user_has_trip_access(user_id, trip_id):
    # Copy lines 1190-1203 from database.py
    pass


def leave_trip(trip_id, user_id):
    # Copy lines 1204-1237 from database.py
    pass
```

#### Step 14: Create `db/trip_invites.py`
```python
"""Trip invitation management."""
from .connection import get_cursor


def invite_user_to_trip(trip_id, inviter_id, invitee_username):
    # Copy lines 1238-1275 from database.py
    pass


def list_trip_invites_for_user(user_id):
    # Copy lines 1276-1293 from database.py
    pass


def has_pending_invite_to_trip(user_id, trip_id):
    # Copy lines 1294-1307 from database.py
    pass


def accept_trip_invite(invite_id, user_id):
    # Copy lines 1308-1338 from database.py
    pass


def decline_trip_invite(invite_id, user_id):
    # Copy lines 1339-1362 from database.py
    pass


def get_trip_collaborators(trip_id):
    # Copy lines 1363-1382 from database.py
    pass
```

#### Step 15: Create `db/trip_gear.py`
```python
"""Trip equipment assignment."""
from .connection import get_cursor


def get_trip_gear_pool(trip_id):
    # Copy lines 1383-1415 from database.py
    pass


def get_trip_assigned_gear(trip_id):
    # Copy lines 1416-1433 from database.py
    pass


def assign_gear_to_trip(trip_id, gear_id):
    # Copy lines 1434-1448 from database.py
    pass


def unassign_gear_from_trip(trip_id, gear_id):
    # Copy lines 1449-1455 from database.py
    pass
```

#### Step 16: Create `db/__init__.py`
This file exports all functions from the modules:

```python
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
from .relationships import get_relationship_status

# Trips
from .trips import (
    create_trip,
    get_trip,
    list_trips_for_user,
    update_trip,
    delete_trip,
    user_has_trip_access,
    leave_trip,
)

# Trip Invites
from .trip_invites import (
    invite_user_to_trip,
    list_trip_invites_for_user,
    has_pending_invite_to_trip,
    accept_trip_invite,
    decline_trip_invite,
    get_trip_collaborators,
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
    'get_user_profile', 'upsert_user_profile',
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
    'get_relationship_status',
    # Trips
    'create_trip', 'get_trip', 'list_trips_for_user',
    'update_trip', 'delete_trip', 'user_has_trip_access', 'leave_trip',
    # Trip Invites
    'invite_user_to_trip', 'list_trip_invites_for_user',
    'has_pending_invite_to_trip', 'accept_trip_invite',
    'decline_trip_invite', 'get_trip_collaborators',
    # Trip Gear
    'get_trip_gear_pool', 'get_trip_assigned_gear',
    'assign_gear_to_trip', 'unassign_gear_from_trip',
]
```

#### Step 17: Update imports in `app.py`

**Change from:**
```python
from database.database import (
    add_gear_item,
    list_gear,
    # ... all other imports
)
```

**Change to:**
```python
from db import (
    add_gear_item,
    list_gear,
    # ... all other imports
)
```

#### Step 18: Update imports in `auth/login.py`

**Change from:**
```python
from database.database import (
    get_user_by_id,
    get_user_by_username,
    create_user,
    user_exists_by_username,
    list_gear,
    list_friends,
    list_trips_for_user,
)
```

**Change to:**
```python
from db import (
    get_user_by_id,
    get_user_by_username,
    create_user,
    user_exists_by_username,
    list_gear,
    list_friends,
    list_trips_for_user,
)
```

#### Step 19: Testing Checklist

After implementing the database refactor, test:

- [ ] User signup
- [ ] User login
- [ ] User logout
- [ ] Add gear item
- [ ] Edit gear item
- [ ] Delete gear item
- [ ] View gear list
- [ ] Send friend request
- [ ] Accept friend request
- [ ] View friends list
- [ ] Create trip
- [ ] Edit trip
- [ ] Delete trip
- [ ] Invite user to trip
- [ ] Accept trip invite
- [ ] View trip dashboard
- [ ] Assign gear to trip
- [ ] Remove gear from trip
- [ ] Add favorite hike
- [ ] View wishlist

#### Step 20: Cleanup

Once all tests pass:
```bash
rm database/database.py
rmdir database  # If empty
```

---

## Part 2: JavaScript Module Split

### Current Structure
```
static/
  └── script.js (1,754 lines)
```

### Target Structure
```
static/js/
  ├── config.js           # API constants
  ├── utils.js            # Utility functions (escapeHtml, etc.)
  ├── auth.js             # Login/logout/register handlers
  ├── dashboard.js        # Dashboard page
  ├── inventory.js        # Gear inventory page
  ├── trips.js            # Trip planner page  
  ├── trip-dashboard.js   # Trip dashboard page
  ├── friends.js          # Friends page
  └── navigation.js       # Global navigation handlers
```

### Line-by-Line Breakdown

#### `js/config.js` (Lines 1-55)
```javascript
// API base URL
export const API_BASE = "https://trailfeathers-github-io-real.onrender.com";

// Gear category mappings
export const REQUIREMENT_KEY_TO_CATEGORY = {
  shelter: "Sleep Systems",
  sleeping_bag: "Sleep Systems",
  // ... rest of lines 4-38
};

// Category order
export const GEAR_CATEGORY_ORDER = [
  "Sleep Systems",
  // ... rest of lines 40-55
];
```

#### `js/utils.js` (Lines 57-175)
```javascript
export function escapeHtml(str) {
  // Lines 57-65
}

export async function loadUserSession() {
  // Lines 67-87
}

export async function loadUserInfo() {
  // Lines 90-108
}

// Weather icon mapping
export function getWeatherIcon(shortForecast) {
  // Lines 110-175
}
```

#### `js/auth.js` (Lines 1-200 of auth section)
Extract login, register, and logout functionality.

```javascript
import { API_BASE } from './config.js';

// Login form handler (lines ~lines around login)
// Register form handler
// Logout button handler (lines 1682-1707)
```

#### `js/inventory.js` (Lines 180-426)
```javascript
import { API_BASE, REQUIREMENT_KEY_TO_CATEGORY, GEAR_CATEGORY_ORDER } from './config.js';
import { escapeHtml } from './utils.js';

// All gear/inventory related code
// Lines 180-426
```

#### `js/trips.js` (Lines 427-850)
```javascript
import { API_BASE } from './config.js';
import { escapeHtml } from './utils.js';

// Trip planner page code
// Lines 427-850
```

#### `js/trip-dashboard.js` (Lines 851-1500)
```javascript
import { API_BASE } from './config.js';
import { escapeHtml, getWeatherIcon } from './utils.js';

// Trip dashboard page code
// Lines 851-1500
```

#### `js/friends.js` (Lines 1501-1650)
```javascript
import { API_BASE } from './config.js';
import { escapeHtml } from './utils.js';

// Friends page code
// Lines 1501-1650
```

#### `js/navigation.js` (Lines 1651-1707)
```javascript
// Global navigation handlers
// Lines 1651-1707
```

### HTML File Updates

**For each HTML file, replace:**
```html
<script src="script.js"></script>
```

**With (example for inventory.html):**
```html
<script type="module">
  import './js/config.js';
  import './js/utils.js';
  import './js/inventory.js';
  import './js/navigation.js';
</script>
```

### Important Notes for JS Refactoring

1. **Use ES6 modules** with `type="module"` in HTML
2. **Export/Import functions** between modules
3. **Event listeners**: Be careful with DOMContentLoaded events across modules
4. **Testing**: Test each page after converting to modules

---

## Part 3: CSS Module Split

### Current Structure
```
static/
  └── styles.css (1,470 lines)
```

### Target Structure
```
static/css/
  ├── main.css          # Imports all other files
  ├── global.css        # Global styles, resets (lines 1-14)
  ├── banner.css        # Banner styles (lines 15-110)
  ├── forms.css         # Form and button styles (lines 111-270)
  ├── dashboard.css     # Dashboard page (lines 271-318)
  ├── inventory.css     # Gear library (lines 319-470)
  ├── trips.css         # Trip planner (lines 471-820)
  ├── trip-dashboard.css # Trip dashboard (lines 821-1170)
  ├── friends.css       # Friends page (lines 1171-1380)
  └── utilities.css     # Utility classes (lines 1381-1470)
```

### Line-by-Line Breakdown

#### `css/main.css`
```css
/* Main CSS file - imports all modules */
@import url('global.css');
@import url('banner.css');
@import url('forms.css');
@import url('dashboard.css');
@import url('inventory.css');
@import url('trips.css');
@import url('trip-dashboard.css');
@import url('friends.css');
@import url('utilities.css');
```

#### `css/global.css` (Lines 1-14)
```css
/* Global styles and resets */
* {
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  background-color: #f7f7f7;
  color: #222;
}
```

#### `css/banner.css` (Lines 15-110)
```css
/* Banner styles */
.banner {
  /* Lines 15-40 */
}

.banner-logo-link {
  /* Lines 41-60 */
}

.banner-logout-btn {
  /* Lines 61-88 */
}

/* Banner variants */
.banner--login { /* ... */ }
.banner--dashboard { /* ... */ }
.banner--inventory { /* ... */ }
/* etc. */
```

#### `css/forms.css` (Lines 111-270)
```css
/* Form and button styles */
input, select, textarea {
  /* Lines 111-150 */
}

button, .btn {
  /* Lines 151-200 */
}

.primary, .secondary, .danger {
  /* Lines 201-270 */
}
```

#### `css/dashboard.css` (Lines 271-318)
```css
/* Dashboard page styles */
.content {
  /* Lines 271-285 */
}

#welcome {
  /* Lines 286-300 */
}

#dash-options {
  /* Lines 301-318 */
}
```

#### `css/inventory.css` (Lines 319-470)
```css
/* Gear library dashboard styles */
.gear-dashboard {
  /* Lines 319-350 */
}

.gear-dashboard-layout {
  /* Lines 351-380 */
}

.gear-category-item {
  /* Lines 381-410 */
}

.btn-delete-gear {
  /* Lines 411-470 */
}
```

#### `css/trips.css` (Lines 471-820)
```css
/* Trip planner styles */
.trip-planner-layout {
  /* Lines 471-520 */
}

.trip-overview {
  /* Lines 521-600 */
}

.trip-card {
  /* Lines 601-700 */
}

#create-trip-form {
  /* Lines 701-820 */
}
```

#### `css/trip-dashboard.css` (Lines 821-1170)
```css
/* Trip dashboard styles */
.trip-dashboard {
  /* Lines 821-900 */
}

.trip-dashboard-section {
  /* Lines 901-1000 */
}

.trip-dashboard-gear-pool {
  /* Lines 1001-1170 */
}
```

#### `css/friends.css` (Lines 1171-1380)
```css
/* Friends page styles */
.friends-dashboard {
  /* Lines 1171-1250 */
}

.friend-request-card {
  /* Lines 1251-1320 */
}

.nav-back {
  /* Lines 1321-1380 */
}
```

#### `css/utilities.css` (Lines 1381-1470)
```css
/* Utility classes and helpers */
.error {
  /* Lines 1381-1400 */
}

.success {
  /* Lines 1401-1420 */
}

.form-hint {
  /* Lines 1421-1470 */
}
```

### HTML File Updates

**Replace in ALL HTML files:**
```html
<link rel="stylesheet" href="styles.css" />
```

**With:**
```html
<link rel="stylesheet" href="css/main.css" />
```

---

## Implementation Order (Recommended)

1. **Database First** (Lowest Risk)
   - Most isolated from frontend
   - Easy to test with existing endpoints
   - Clear module boundaries

2. **CSS Second** (Low Risk)
   - Visual changes are immediately visible
   - Easy to revert if issues occur
   - No logic to break

3. **JavaScript Last** (Higher Risk)
   - Most complex dependencies
   - Requires module system understanding
   - Needs extensive testing

---

## Testing Strategy

### After Each Module:

1. **Unit Testing**
   - Test each function independently
   - Verify imports work correctly

2. **Integration Testing**
   - Test full user flows
   - Check all pages load correctly

3. **Browser Testing**
   - Clear cache completely
   - Test in Chrome/Firefox/Safari
   - Check console for errors

### Rollback Plan

If issues occur after refactoring a module:

1. **Keep backups**: Before starting, copy the original files
2. **Git commits**: Commit after each successful module
3. **Revert**: Use `git revert` or restore from backup if needed

---

## Benefits After Refactoring

1. **Maintainability**: Easier to find and fix bugs
2. **Collaboration**: Multiple developers can work on different modules
3. **Code Reuse**: Import only what you need
4. **Testing**: Test modules independently
5. **Performance**: Load only necessary CSS/JS per page (future optimization)

---

## Estimated Time

- **Database refactor**: 2-3 hours
- **CSS refactor**: 1-2 hours  
- **JavaScript refactor**: 3-4 hours
- **Testing**: 2-3 hours
- **Total**: 8-12 hours

---

## Questions or Issues?

If you encounter any issues during refactoring:

1. Check import paths are correct
2. Verify all functions are exported from modules
3. Check browser console for errors
4. Refer back to line numbers in this document

---

**Good luck with the refactoring! Take it one module at a time and test thoroughly.**
