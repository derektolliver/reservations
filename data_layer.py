from enum import Enum
from datetime import datetime, timedelta
import uuid

class Status(Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    CONFIRMED = "CONFIRMED"

# In-memory data structure
# This could instead be a class supporting these functions
# But I am choosing this approach for a simple implementation
# as well as the ability to swap this out for a database later.
# Imagine this could instead be table in a database with the following columns:
# time_slot_id, provider_id, client_id, timestamp, duration, status
# Could have other tables for providers, clients, etc.
# This could later support dual writes, backfills, etc. before swapping to a db

curr_date = None

"""
This structure is a dictionary where the keys are dates and the values are
a nested map where the keys are time slots (datetimes each incremented by 15 minutes)
and the values are dictionaries. The values in the inner dictionary are the
provider_id, an optional client_id, timestamp, duration, and status of the time slot.
"""
time_slots = {}

# Helper function to generate time slots
def generate_time_slots(start_time, end_time):
    """Generate a list of time slots between start_time and end_time.

    This function generates time slots of 15 minutes each, starting from
    start_time and ending before end_time.

    Args:
        start_time (datetime): The starting time for generating time slots.
        end_time (datetime): The ending time for generating time slots.

    Returns:
        list of datetime: A list of datetime objects representing the time slots.
    """
    slots = []
    current_time = start_time
    while current_time < end_time:
        slots.append(current_time)
        current_time += timedelta(minutes=15)

    return slots

# Availability CRUD operations
def add_availability(provider_id, start_time, end_time):
    """Add availability for a provider to our data store.

    Args:
        provider_id (str): The ID of the provider.
        start_time (datetime): The starting datetime of availability.
        end_time (datetime): The ending datetime of availability.
    """
    global time_slots

    # Ensure start_time and end_time are on the same date
    if start_time.date() != end_time.date():
        raise ValueError("start_time and end_time must be on the same date")

    slots = generate_time_slots(start_time, end_time)
    
    for slot in slots:
        date_key = slot.date()
        if date_key not in time_slots:
            time_slots[date_key] = {}
        if slot not in time_slots[date_key]:
            time_slots[date_key][slot] = {}
        
        # Ensure the provider does not already have availability at this time
        previously_booked = False
        for i in time_slots[date_key][slot]:
            if time_slots[date_key][slot][i]["provider_id"] == provider_id:
                previously_booked = True

        if not previously_booked:
            time_slots[date_key][slot][uuid.uuid4().hex] = {
                "provider_id": provider_id,
                "timestamp": slot,
                "duration": timedelta(minutes=15),
                "status": Status.AVAILABLE,
                "last_updated": datetime.now()
            }

def get_availability(start_time, end_time, provider_id=None):
    """Get availability between a start and end time. Optionally filter by provider.
    # TODO: Support getting availability for a range of days
    # TODO: Support getting availability for multiple providers

    Args:
        start_time (datetime.date): The start time to check availability for.
        end_time (datetime.date): The end time to check availability for.
        provider_id (str): The ID of the provider.

    Returns:
        list: A list of availability slots for the provider on the specified day.
    """

    date = start_time.date()
    times = generate_time_slots(start_time, end_time)
    availability = []

    if date in time_slots:
        for t in times:
            if t in time_slots[date]:
                slot = time_slots[date][t]
                for slot_id, slot_info in slot.items():
                    if provider_id is None or slot["provider_id"] == provider_id and slot["status"] == Status.AVAILABLE:
                        slot = {
                            "timeSlotId": slot_id,
                            "providerId": slot_info["provider_id"],
                            "timestamp": str(slot_info["timestamp"]),
                            "duration": str(slot_info["duration"].total_seconds() // 60),
                            "status": str(slot_info["status"].value),
                            "lastUpdated": str(slot_info["last_updated"])
                        }

                        if "client_id" in slot_info:
                            slot["clientId"] = slot_info["client_id"]
    
                        availability.append(slot)
    return availability

# Reservation CRUD operations
def reserve_time_slot(time_slot_id, timestamp, client_id):
    """Add a reservation for a time slot at a specific timestamp.

    Args:
        provider_id (str): The ID of the provider.
        timestamp (datetime): The specific timestamp to add a reservation.
        client_id (str, optional): The ID of the client making the reservation.
    """
    global time_slots
    date_key = timestamp.date()
    if date_key in time_slots and timestamp in time_slots[date_key] and time_slot_id in time_slots[date_key][timestamp]:
        if time_slots[date_key][timestamp][time_slot_id]["status"] == Status.RESERVED and time_slots[date_key][timestamp][time_slot_id]["last_updated"] < datetime.now() - timedelta(minutes=30):
            time_slots[date_key][timestamp][time_slot_id]["status"] = Status.AVAILABLE
            time_slots[date_key][timestamp][time_slot_id]["last_updated"] = datetime

            if "client_id" in time_slots[date_key][timestamp][time_slot_id]:
                del time_slots[date_key][timestamp][time_slot_id]["client_id"]

        if time_slots[date_key][timestamp][time_slot_id]["status"] == Status.AVAILABLE:
            time_slots[date_key][timestamp][time_slot_id]["status"] = Status.RESERVED
            time_slots[date_key][timestamp][time_slot_id]["client_id"] = client_id
            time_slots[date_key][timestamp][time_slot_id]["last_updated"] = datetime.now()

            # Setup for testing 30 minute expiration
            # time_slots[date_key][timestamp][time_slot_id]["last_updated"] = datetime.now() - timedelta(minutes=30)

        return True
    
    return False

def get_reservation(time_slot_id, timestamp):
    """Get a reservation for a provider by time slot ID.

    Args:
        provider_id (str): The ID of the provider.
        time_slot_id (str): The ID of the time slot.

    Returns:
        dict or None: The reservation slot if found, otherwise None.
    """
    date_key = timestamp.date()
    if date_key in time_slots and timestamp in time_slots[date_key] and time_slot_id in time_slots[date_key][timestamp]:
            return time_slots[date_key][timestamp][time_slot_id]
    return None

def update_reservation_status(timestamp, time_slot_id):
    """Update the status of a reservation for a provider by time slot ID.

    Args:
        provider_id (str): The ID of the provider.
        time_slot_id (str): The ID of the time slot.
        status (Status): The new status of the reservation.
    """
    date_key = timestamp.date()
    if date_key in time_slots and timestamp in time_slots[date_key] and time_slot_id in time_slots[date_key][timestamp]:
        slot = time_slots[date_key][timestamp][time_slot_id]
        if slot["status"] == Status.RESERVED:
                if slot["last_updated"] >= datetime.now() - timedelta(minutes=30):
                    slot["status"] = Status.CONFIRMED
                    slot["last_updated"] = datetime.now()
                    return True
                else:
                    slot["status"] = Status.AVAILABLE
                    slot["last_updated"] = datetime.now()
    
    return False
            
                

def cleanup_old_reservations():
    """
    Cleanup old reservations that are past the current time and have RESERVED status.
    
    This could be improved if we tracked the "RESERVED" slots separately.
    Could have a map of timeslots (datetime) to a list of time_slot_ids.
    When a reserved timeslot becomes 30 minutes old, we can look through all time_slot_ids
    and remove them from the time_slots map iff they are still in a "RESERVED" status.
    """
    global time_slots
    now = datetime.now()
    for date_key in list(time_slots.keys()):
        # Remove all old RESERVED slots before today
        # Do we want to run this every time? It will create a lot of extra cycles
        # on every cleanup operation. It should only needs to be run once a day.
        # track current date. When date changes, run this again. Ideally on its own, separate thread
        for timestamp in list(time_slots[date_key].keys()):
            if timestamp < now and time_slots[date_key][timestamp]["status"] == Status.RESERVED:
                del time_slots[date_key][timestamp]
        if not time_slots[date_key]:
            del time_slots[date_key]