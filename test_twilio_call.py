"""Test Twilio call to debug issue"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_PHONE_NUMBER')

client = Client(account_sid, auth_token)

# Get account info
account = client.api.accounts(account_sid).fetch()
print(f"Account Status: {account.status}")
print(f"Account Type: {account.type}")

# Check if trial
if account.type == 'Trial':
    print("\n⚠️  TRIAL ACCOUNT DETECTED")
    print("Trial accounts can only call verified phone numbers.")
    print("\nTo verify a number:")
    print("1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/verified")
    print("2. Click 'Add a new number'")
    print("3. Enter +917666815841 and verify via SMS")
    
    # Get verified numbers
    print("\n✅ Currently Verified Numbers:")
    try:
        validated_numbers = client.outgoing_caller_ids.list()
        for number in validated_numbers:
            print(f"   - {number.phone_number}")
    except Exception as e:
        print(f"   Error fetching verified numbers: {e}")

# Get recent calls to see what happened
print("\n📞 Recent Calls:")
calls = client.calls.list(limit=5)
for call in calls:
    print(f"   {call.sid}: {call.to} -> Status: {call.status}")
    if call.status in ['failed', 'busy', 'no-answer']:
        # Try to get error details
        if hasattr(call, 'error_message') and call.error_message:
            print(f"      Error: {call.error_message}")
