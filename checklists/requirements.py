"""
Checklists are now stored in the database (requirement_types + activity_requirements).
Use GET /api/trips/<id>/checklist for trip requirements and GET /api/requirement-types for gear types.
Legacy: empty dict for any code that still imports CHECKLISTS.
"""
CHECKLISTS = {}
