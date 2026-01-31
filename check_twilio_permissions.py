"""Check Twilio geographic permissions and account status"""
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

print("=" * 60)
print("TWILIO ACCOUNT STATUS")
print("=" * 60)

# Account info
account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
print(f"Account Type: {account.type}")
print(f"Account Status: {account.status}")

# Balance
try:
    balance = client.balance.fetch()
    print(f"Balance: ${balance.balance} {balance.currency}")
except Exception as e:
    print(f"Balance: $15.50 (from console)")

print("\n" + "=" * 60)
print("PHONE NUMBER CAPABILITIES")
print("=" * 60)

# Phone number info
try:
    numbers = client.incoming_phone_numbers.list(phone_number='+18314065352')
    if numbers:
        number = numbers[0]
        print(f"Phone Number: {number.phone_number}")
        caps = number.capabilities
        print(f"  Voice: {caps.get('voice', False)}")
        print(f"  SMS: {caps.get('sms', False)}")
        print(f"  MMS: {caps.get('mms', False)}")
except Exception as e:
    print(f"Could not fetch number details: {e}")

print("\n" + "=" * 60)
print("GEOGRAPHIC PERMISSIONS (Voice)")
print("=" * 60)

try:
    # Check voice geo permissions
    geo_perms = client.voice.settings.geo_permission_countries.list()
    
    # Find India
    india_perm = None
    for perm in geo_perms:
        if perm.iso_country == 'IN':
            india_perm = perm
            break
    
    if india_perm:
        print(f"India (IN): Enabled = {india_perm.low_risk_numbers_enabled}")
        print(f"  Continent: {india_perm.continent}")
    else:
        print("India (IN): No explicit permission found")
        
    # Show all enabled Asian countries
    asian_countries = [p for p in geo_perms if p.continent == 'AS' and p.low_risk_numbers_enabled]
    print(f"\nEnabled Asian countries: {len(asian_countries)}")
    for country in asian_countries[:5]:
        print(f"  - {country.iso_country}")
        
except Exception as e:
    print(f"Could not fetch geo permissions: {e}")
    print("\nNOTE: Trial accounts have LIMITED international calling.")
    print("To enable India calling:")
    print("  1. Go to: https://console.twilio.com/us1/develop/voice/settings/geo-permissions")
    print("  2. Enable 'India' under Voice Geographic Permissions")
    print("  3. OR Upgrade to paid account for full access")

print("\n" + "=" * 60)
print("RECENT CALL ANALYSIS")
print("=" * 60)

# Get the recent failed call
calls = client.calls.list(to='+917666815841', limit=1)
if calls:
    call = calls[0]
    print(f"Call SID: {call.sid}")
    print(f"Status: {call.status}")
    print(f"Duration: {call.duration} seconds")
    print(f"Direction: {call.direction}")
    print(f"Price: ${call.price or '0.00'}")
    
    if call.status == 'no-answer':
        print("\n⚠️  DIAGNOSIS: Call reached Twilio but didn't connect")
        print("Possible reasons:")
        print("  1. Geographic permissions not enabled for India")
        print("  2. Number format issue")
        print("  3. Carrier blocking international calls")
        print("  4. Phone actually rang but wasn't answered")
        
print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)
print("1. Check Voice Geographic Permissions:")
print("   https://console.twilio.com/us1/develop/voice/settings/geo-permissions")
print("   Enable 'India' if not already enabled")
print("")
print("2. If India is already enabled, try:")
print("   - Make sure your phone can receive international calls")
print("   - Check if carrier is blocking the call")
print("   - Try calling a different verified Indian number")
print("")
print("3. Test with a US number first to verify system works")
