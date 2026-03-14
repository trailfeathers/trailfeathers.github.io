"""
TrailFeathers - Activity requirements and requirement types; get_trip_requirement_summary for dashboard checklist.
Group: TrailFeathers
Authors (alphabetically by last name): Kim, Smith, Domst, and Snider
Last updated: 3/13/26
"""
from .connection import get_cursor


def list_requirement_types():
    """Return all requirement types: id, key, display_name. Ordered by display_name."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT id, key, display_name FROM requirement_types
               ORDER BY display_name""",
        )
        return cur.fetchall()


def list_activity_requirements(activity_type):
    """Return requirements for an activity: id, requirement_type_id, rule, quantity, n_persons,
       plus requirement type key and display_name from requirement_types."""
    with get_cursor() as cur:
        cur.execute(
            """SELECT ar.id, ar.requirement_type_id, ar.rule, ar.quantity, ar.n_persons,
                      rt.key AS requirement_key, rt.display_name AS requirement_display_name
               FROM activity_requirements ar
               JOIN requirement_types rt ON rt.id = ar.requirement_type_id
               WHERE ar.activity_type = %s
               ORDER BY rt.display_name""",
            (activity_type,),
        )
        return cur.fetchall()


def _required_count_for_rule(rule, quantity, n_persons, num_people):
    """Compute required count given rule and head count."""
    import math
    if rule == "per_group":
        return quantity
    if rule == "per_person":
        return quantity * num_people
    if rule == "per_N_persons" and n_persons and n_persons > 0:
        return quantity * math.ceil(num_people / n_persons)
    return 0


def _covered_count_for_type(assigned_gear_rows):
    """From list of gear rows (with capacity_persons), sum coverage. Group-shareable (NULL) counts as 1 per type."""
    if not assigned_gear_rows:
        return 0
    total = 0
    for row in assigned_gear_rows:
        cap = row.get("capacity_persons")
        if cap is not None:
            total += cap
        else:
            total += 1
    return total


def get_trip_requirement_summary(trip_id):
    """For the trip's activity, return list of requirement rows with required_count, covered_count, status.
    Each row: requirement_type_id, requirement_key, requirement_display_name, rule, quantity, n_persons,
    required_count, covered_count, status ('met' | 'short').
    
    NOTE: This function imports from trips module to avoid circular dependency issues.
    """
    # Import here to avoid circular dependency
    from .trips import get_trip
    from .trip_invites import list_trip_collaborators
    
    trip = get_trip(trip_id)
    if not trip:
        return None
    activity_type = (trip.get("activity_type") or "").strip()
    if not activity_type:
        return []
    reqs = list_activity_requirements(activity_type)
    if not reqs:
        return []

    # Head count
    collabs = list_trip_collaborators(trip_id)
    num_people = len(collabs)

    # Assigned gear for this trip, with requirement_type_id and capacity_persons
    with get_cursor() as cur:
        cur.execute(
            """SELECT g.id, g.requirement_type_id, g.capacity_persons
               FROM trip_gear tg
               JOIN gear g ON g.id = tg.gear_id
               WHERE tg.trip_id = %s""",
            (trip_id,),
        )
        assigned = cur.fetchall()

    # Group assigned gear by requirement_type_id
    by_type = {}
    for row in assigned:
        rt_id = row.get("requirement_type_id")
        if rt_id is not None:
            by_type.setdefault(rt_id, []).append(row)

    out = []
    for ar in reqs:
        rt_id = ar["requirement_type_id"]
        rule = ar["rule"]
        quantity = ar["quantity"]
        n_persons = ar.get("n_persons")
        required = _required_count_for_rule(rule, quantity, n_persons, num_people)
        covered = _covered_count_for_type(by_type.get(rt_id, []))
        status = "met" if covered >= required else "short"
        out.append({
            "requirement_type_id": rt_id,
            "requirement_key": ar["requirement_key"],
            "requirement_display_name": ar["requirement_display_name"],
            "rule": rule,
            "quantity": quantity,
            "n_persons": n_persons,
            "required_count": required,
            "covered_count": covered,
            "status": status,
        })
    return out
