BASE_REQUIREMENTS = {
    "DAY_HIKE": [
        {"type": "BACKPACK", "capacity": False},
        {"type": "CLOTHING", "capacity": False},
        {"type": "NAVIGATION", "capacity": False},
        {"type": "FIRST_AID", "capacity": False},
        {"type": "WATER_TREATMENT", "capacity": False},
        {"type": "LIGHT_SOURCE", "capacity": False},
    ],

    "BACKPACKING": [
        {"type": "BACKPACK", "capacity": False},
        {"type": "SHELTER", "capacity": True, "capacity_field": "capacity_people"}, 
        {"type": "SLEEPING_BAG", "capacity": False},
        {"type": "SLEEPING_PAD", "capacity": False},
        {"type": "COOK_SET", "capacity": False},
        {"type": "WATER_TREATMENT", "capacity": False},
        {"type": "NAVIGATION", "capacity": False},
        {"type": "FIRST_AID", "capacity": False},
        {"type": "LIGHT_SOURCE", "capacity": False},
        {"type": "CLOTHING", "capacity": False},
    ],

    "CAR_CAMPING": [
        {"type": "SHELTER", "capacity": True, "capacity_field": "capacity_people"},
        {"type": "SLEEPING_BAG", "capacity": False},
        {"type": "SLEEPING_PAD", "capacity": False},
        {"type": "COOK_SET", "capacity": False},
        {"type": "FOOD_STORAGE", "capacity": False},
        {"type": "LIGHT_SOURCE", "capacity": False},
    ],

    "MOUNTAINEERING": [
        {"type": "BACKPACK", "capacity": False},
        {"type": "SHELTER", "capacity": True, "capacity_field": "capacity_people"},
        {"type": "SLEEPING_BAG", "capacity": False},
        {"type": "SLEEPING_PAD", "capacity": False},
        {"type": "COOK_SET", "capacity": False},
        {"type": "WATER_TREATMENT", "capacity": False},
        {"type": "NAVIGATION", "capacity": False},
        {"type": "FIRST_AID", "capacity": False},
        {"type": "LIGHT_SOURCE", "capacity": False},
        {"type": "CLOTHING", "capacity": False},
        {"type": "TECHNICAL_GEAR", "capacity": False},
    ],

    "TRAIL_RUNNING": [
        {"type": "RUNNING_PACK", "capacity": False},
        {"type": "CLOTHING", "capacity": False},
        {"type": "NAVIGATION", "capacity": False},
        {"type": "WATER_TREATMENT", "capacity": False},
        {"type": "LIGHT_SOURCE", "capacity": False},
        {"type": "FIRST_AID", "capacity": False},
    ],
}
