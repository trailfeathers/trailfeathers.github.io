# TrailFeathers — Product Requirements Document (PRD)

**Authors:** Dash Kim, James Smith, Lachlan Domst, Kellen Snider  
**Version:** 1.0  
**Last Updated:** February 2026

---

## 1. Product Overview

### 1.1 Vision

TrailFeathers is a web-based outdoor trip planning application that helps users maintain personal gear inventories, plan trips collaboratively, and access AI-summarized trail and weather information—all in one platform. The product aims to reduce redundant packing, improve safety through structured checklists and condition awareness, and centralize coordination that today happens across spreadsheets, group chats, and scattered web sources.

### 1.2 Problem Statement

Outdoor trip planning is fragmented and risky:

- **Gear:** Most people do not keep a shareable, comparable inventory. Necessary items (e.g., water filtration, cook systems) are often overlooked; search and rescue data cite inadequate equipment and poor planning as leading causes of incidents.
- **Coordination:** Trips are planned via informal channels (text, docs). There is no single place to see who brings what, leading to duplication or gaps.
- **Conditions:** Trail and weather information is scattered, quickly outdated, and sometimes behind paywalls. Environmental factors (e.g., bridge out, storms) can change faster than static sources update.

No existing tool unifies **personal gear inventory**, **collaborative trip planning**, **automated safety checklists**, and **summarized location intelligence** in one system.

### 1.3 Solution Summary

TrailFeathers provides:

1. **Personal gear inventory** — Users log gear (type, name, capacity, weight, brand, condition, notes) and view it in one place.
2. **Trip creation and collaboration** — Users create trips (name, trail, activity type, intended start date), invite friends as collaborators, and (planned) assign gear to trips and people.
3. **Friends and trip invites** — Users send/accept/decline friend requests; trip creators invite friends to trips; invitees accept/decline.
4. **AI-powered location intelligence (planned)** — For a trip location, the system fetches public data (e.g., WTA, Oregon Hikers, weather), summarizes it via an LLM, and surfaces conditions and safety-relevant insights.

The system is designed to remain useful even in a **degraded mode**: if AI integration is unavailable, the core value is still gear planning and collaboration.

---

## 2. Goals and Success Metrics

| Goal | Success Metric |
|------|----------------|
| Reduce gear-related planning risk | Users maintain inventories and use trip checklists; missing-gear alerts (when implemented) are acted on. |
| Centralize trip coordination | Trips are created with collaborators; gear is assigned to trips/people (when implemented). |
| Improve condition awareness | Users view AI summaries for trip locations (when implemented); errors/unavailable data are clearly indicated. |
| Operate within scope and cost | System supports up to 500 total users, ~25 concurrent at peak; 95% of requests complete in under 2 seconds; ~15 requests/sec at peak. |

---

## 3. User Classes and Personas

| User Class | Description | Responsibilities | Technical Expectation |
|------------|-------------|-----------------|------------------------|
| **Outdoor recreationists** | Hikers, backpackers, trail runners, bird watchers, mountaineers, skiers, snowshoers, etc. | Maintain gear inventory; create/join trips; manage group gear; review AI summaries. | General computer use; no special technical skills. |
| **Data providers** | WTA, Oregon Hikers, weather services, etc. | None (external). | N/A — data consumed by system, not entered by them. |
| **System administrators** | Backend/ops | User and permission management; API/integration management; monitoring. | Strong technical skills. |

---

## 4. Features and Requirements

### 4.1 Feature Summary

| # | Feature | Priority | Status |
|---|---------|----------|--------|
| F1 | User authentication (signup, login, logout, session) | P0 | Done |
| F2 | Personal gear inventory (CRUD, list by user) | P0 | Done (add/list; edit/delete as enhancement) |
| F3 | Friends (request, accept/decline, list friends) | P0 | Done |
| F4 | Trips (create, list, get detail, collaborators) | P0 | Done |
| F5 | Trip invites (invite friends, list pending, accept/decline) | P0 | Done |
| F6 | Trip–gear assignment (“who brings what”) | P1 | Schema done; API/UI TBD |
| F7 | Packing lists and missing-gear alerts per trip | P1 | Planned |
| F8 | AI summary (trail/weather from public sources + LLM) | P1 | Planned |
| F9 | In-app communication between trip members | P2 | Future |

### 4.2 Functional Requirements (from SRS and description)

- **FR1 — Gear inventory**
  - User can add gear with required: type (from predetermined set), name; optional: capacity, weight, brand, condition, notes.
  - User can view their full inventory.
  - Data stored in DB and reflected in UI (and via API).

- **FR2 — Trip creation**
  - User can create a trip with: trip name, trail name, activity type, intended start date.
  - User can view trips they created or collaborate on.
  - Only trip creator can invite collaborators; only friends can be invited.

- **FR3 — Collaboration**
  - Trip creator invites by username or user_id; invitee sees invite and can accept or decline.
  - On accept, user is added as trip collaborator; both creator and collaborators can access trip and (when built) trip gear.

- **FR4 — AI summary (planned)**
  - For a given trip, system uses location/trail name to fetch public data (trip reports, weather).
  - Data is summarized via LLM and shown in-app; unavailable or errors are clearly indicated; caching for frequent locations is desired.

### 4.3 External Interfaces (Data Formats)

- **Gear:** POST JSON, e.g. `{"type": "Sleep System", "name": "2-person tent", "weight": "N/A", "brand": "Mountain Hardware", "condition": "like new"}`. Type from enumerations; name/capacity length constraints (e.g., 1–50 chars); optional fields as specified.
- **Trip:** POST JSON, e.g. `{"tripName": "...", "trailName": "...", "activityType": "Backpacking", "intendedStartDate": "..."}`. Trip and trail names 1–100 chars; activity type from enum; dates as ISO datetime.
- **Collaborators/invites:** Invite by `user_id` or `username` in payload; responses return standard JSON with `ok`, `id`, or `error` as appropriate.

### 4.4 Non-Functional Requirements

- **Usability:** New users can sign up, build a gear checklist, create/join trips, and (when available) see AI summaries and missing-gear alerts. All without special technical skill.
- **Performance:** Up to 500 users; ~25 concurrent; 95% of requests &lt; 2 s; ~15 req/s peak.
- **Security & privacy:** Passwords hashed (e.g., bcrypt); sessions HTTPOnly, appropriate SameSite/Secure. User data (including gear) not visible to others unless shared via trip collaboration; users control what is shared per trip.
- **Reliability:** Shared inventories, checklists, and summaries must be consistent and available; incomplete or unavailable data must be clearly indicated so users are not misled.

---

## 5. Use Cases (Summary)

1. **Maintain personal gear inventory** — User logs in → “My Gear” → Add item (type, name, optional fields) → system validates and saves → inventory view updates.
2. **Plan a trip** — User with gear creates trip (activity, location, date) → optionally invites friends → (when built) collaborators’ gear is combined, users assign items to trip → system generates per-user packing lists and missing-gear alerts.
3. **Review trip conditions** — User opens trip → “AI report” → system resolves location, fetches public data, summarizes via LLM → user sees summary (or clear error/unavailable message).

---

## 6. System Context and Architecture

- **Frontend:** HTML/CSS/JS (e.g., GitHub Pages); login, inventory, trips, dashboard, collaborative views.
- **Backend:** Flask (Python); session-based auth; REST API; business logic for gear, friends, trips, invites.
- **Database:** PostgreSQL (e.g., Neon); tables: users, gear, trips, trip_collaborators, trip_invites, trip_gear, friend_requests.
- **AI (planned):** Scrape/source public trip reports and weather; LLM API for summarization; results and errors surfaced in UI.

Deployment: Backend on Render; frontend on GitHub Pages; CORS and cookie settings (e.g., SameSite=None, Secure) for cross-origin sessions.

---

## 7. Out of Scope (Current PRD)

- Native mobile apps (web-first).
- Direct integration with e-commerce or gear marketplaces.
- Real-time chat or streaming condition updates (P2 in-app communication is future).
- Storing full trail/weather datasets in DB (prefer fetch/summarize/cache to limit storage).

---

## 8. Dependencies and Constraints

- **External:** Public trail reports (e.g., WTA, Oregon Hikers), weather services; availability and rate limits affect AI feature.
- **Technical:** Flask, PostgreSQL, frontend hosting and CORS/session configuration; AI API availability and cost.
- **Operational:** Admin must manage user accounts, permissions, and API/integration health; backup/degraded mode (e.g., no AI) must still deliver core gear and trip value.

---

## 9. References

- **Project description:** `documents/description.docx`
- **Software Requirements Specification:** `documents/SRS.docx`
- **Database schema:** `database/schema.sql`
- **Backend API:** `app.py` and related modules

---

*This PRD aligns with the SRS and project description and is intended to guide development and prioritization (P0/P1/P2) for TrailFeathers.*
