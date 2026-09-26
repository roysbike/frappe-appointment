def with_booked_intervals(calendar_slots, booked):
    """Busy blocks plus already booked meetings, earliest start first."""
    combined = list(calendar_slots or [])
    for item in booked or []:
        start = item.get("starts_on")
        end = item.get("ends_on")
        if start and end and end > start:
            combined.append({"starts_on": start, "ends_on": end})
    combined.sort(key=lambda slot: (slot["starts_on"], slot["ends_on"]))
    return combined
