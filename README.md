# TrailFeathers

TrailFeathers is a web-based backpacking trip planner designed to help outdoor recreationists organize gear and plan collaborative trips.

## Overview

TrailFeathers allows users to:

- Digitally store and manage personal gear inventories
- Create and save trip plans
- Add collaborators to trips
- Generate AI-powered summaries of trip reports and location conditions

The system is built around a relational database (PostgreSQL) and integrates AI-generated summaries to provide relevant planning insights.

---

## Core Features

### Gear Inventory
Users can:
- Add, edit, and manage personal gear items
- Categorize gear (e.g., Sleep System, Cookware, Bag)
- Store optional gear attributes (weight, brand, condition)

### Trip Creation
Users can:
- Create trips with a trail name and activity type
- Set intended start dates
- Add collaborators
- Save trips for later planning

### AI Summary
For each saved trip, the system:
- Retrieves the trail name from the database
- Gathers relevant trip report information
- Generates a summarized overview for the user


