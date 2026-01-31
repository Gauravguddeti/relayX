import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

# Get the most recent call
call_sid = "CA133efdce3c14fdd98f990fbce9f48501"

print(f"Fetching call details for {call_sid}...")
call = client.calls(call_sid).fetch()

print(f"\nCall Status: {call.status}")
print(f"Direction: {call.direction}")
print(f"Duration: {call.duration} seconds")
print(f"Start Time: {call.start_time}")
print(f"End Time: {call.end_time}")
print(f"Price: {call.price} {call.price_unit}")
print(f"\nFrom: {call.from_}")
print(f"To: {call.to}")
print(f"\nAnswered By: {call.answered_by}")

# Check for any errors or warnings
if hasattr(call, 'error_code') and call.error_code:
    print(f"\n❌ ERROR CODE: {call.error_code}")
    print(f"Error Message: {call.error_message}")

# Get call events
print("\n--- Call Events ---")
events = client.calls(call_sid).events.list(limit=20)
for event in events:
    print(f"{event.timestamp}: {event.name} - {event.request}")
