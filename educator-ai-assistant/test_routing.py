#!/usr/bin/env python3

# Test the specific routing logic to see what's happening

def test_routing_logic():
    """Test the actual routing logic"""
    
    test_commands = [
        "Send marks to Section A parents",
        "Mark attendance for Section B", 
        "Schedule staff meeting for Friday"
    ]
    
    for command in test_commands:
        print(f"\n=== Testing: '{command}' ===")
        command_lower = command.lower()
        
        # Test explicit routing conditions
        print(f"Command lower: '{command_lower}'")
        
        # Test bulk communication routing
        bulk_comm_condition1 = 'send' in command_lower and ('section' in command_lower or 'class' in command_lower or 'all' in command_lower or 'parents' in command_lower)
        bulk_comm_condition2 = 'send' in command_lower and ('marks' in command_lower or 'grades' in command_lower)
        print(f"Bulk communication condition 1 (send + section/class/all/parents): {bulk_comm_condition1}")
        print(f"Bulk communication condition 2 (send + marks/grades): {bulk_comm_condition2}")
        print(f"Should route to BULK_COMMUNICATION: {bulk_comm_condition1 or bulk_comm_condition2}")
        
        # Test attendance routing
        attendance_condition = 'attendance' in command_lower or ('mark' in command_lower and 'attendance' in command_lower)
        print(f"Attendance condition: {attendance_condition}")
        print(f"Should route to ATTENDANCE: {attendance_condition}")
        
        # Test staff meeting routing
        staff_condition = ('staff' in command_lower and 'meeting' in command_lower) or ('schedule' in command_lower and ('staff' in command_lower or 'department' in command_lower))
        print(f"Staff meeting condition: {staff_condition}")
        print(f"Should route to STAFF_MEETING: {staff_condition}")

if __name__ == "__main__":
    test_routing_logic()