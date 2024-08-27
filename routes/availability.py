from flask import Blueprint, request, jsonify
from data_layer import add_availability, get_availability, reserve_time_slot, get_reservation, update_reservation_status, cleanup_old_reservations, Status
from utils.formatter import DAY_IN_SECONDS, validate_timestamp, format_timestamp
from datetime import datetime

availability_bp = Blueprint('clients', __name__)

@availability_bp.route('/availability', methods=['POST'])
def submit_availability():
    """Submit availability for a provider.

    Expected JSON format:
    {
        "providerId": "string", (uuid)
        "startTime": "string", (datetime)
        "endTime": "string" (datetime)
    }
    """
    data = request.json
    provider_id = data.get('providerId')
    start = data.get('startTime')
    end = data.get('endTime')

    if not validate_timestamp(start) or not validate_timestamp(end):
        return jsonify({"message": "Invalid timestamp format"}), 400

    add_availability(provider_id, format_timestamp(start), format_timestamp(end))
    return jsonify({"message": "Availability submitted successfully"}), 200

@availability_bp.route('/availability', methods=['GET'])
def get_availability_route():
    """Get availability between some start and end time.

    Expected query parameters:
    - startTime: The start time of the availability. (datetime)
    - endTime: The end time of the availability. (datetime)
    """
    cleanup_old_reservations()
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')

    if not validate_timestamp(start_time) or not validate_timestamp(end_time):
        return jsonify({"message": "Invalid timestamp format"}), 400

    available_slots = get_availability(format_timestamp(start_time), format_timestamp(end_time))
    return jsonify({"availableTimeSlots": available_slots}), 200

@availability_bp.route('/availability/reserve', methods=['POST'])
def reserve_slot():
    """Reserve a time slot. For use by clients to reserve time with an associated provider.

    Expected JSON format:
    {
        "timeSlotId": "string", (uuid)
        "timeSlot": "string", (datetime)
        "clientId": "string" (uuid)
    }
    """
    cleanup_old_reservations()
    data = request.json
    time_slot_id = data.get('timeSlotId')
    time_slot = data.get('timeSlot')
    client_id = data.get('clientId')

    if not validate_timestamp(time_slot):
        return jsonify({"message": "Invalid timestamp format"}), 400
    
    if (format_timestamp(time_slot) - datetime.now()).total_seconds() < DAY_IN_SECONDS:
        return jsonify({"message": "Time slot must be at least 24 hours in the future"}), 400

    reserved = reserve_time_slot(time_slot_id, format_timestamp(time_slot), client_id)
    if reserved:
        return jsonify({"message": "Time slot reserved successfully"}), 200
    else:
        return jsonify({"message": "Time slot not available"}), 400

@availability_bp.route('/availability/confirm/<time_slot_id>', methods=['PUT'])
def confirm_reservation(time_slot_id):
    """Confirm a reservation for a time slot.

    Args:
        time_slot_id (string): time slot ID to confirm.

    Expected JSON format:
    {
        "timeSlot": "string" (datetime)
    }
    """
    cleanup_old_reservations()
    data = request.json
    time_slot = data.get('timeSlot')

    if not validate_timestamp(time_slot):
            return jsonify({"message": "Invalid timestamp format"}), 400

    reservation = get_reservation(time_slot_id, format_timestamp(time_slot))
    if reservation:
        if reservation["status"] == Status.RESERVED:
            if update_reservation_status(reservation["timestamp"], time_slot_id):
                return jsonify({"message": "Reservation confirmed successfully"}), 200
            else:
                return jsonify({"message": "Reservation cannot be confirmed"}), 400
        elif reservation["status"] == Status.CONFIRMED:
            return jsonify({"message": "Reservation already confirmed"}), 200
        else: # Status is not RESERVED or CONFIRMED, so it must be AVAILABLE
            return jsonify({"message": "Reservation cannot be confirmed"}), 400
    else:
        return jsonify({"message": "Reservation not found"}), 404