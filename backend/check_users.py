from shared.database import SupabaseDB

db = SupabaseDB()
result = db.client.table('users').select('*').execute()

print('\n=== USERS IN DATABASE ===\n')
for user in result.data:
    print(f"ID: {user['id']}")
    print(f"Email: {user['email']}")
    print(f"Name: {user.get('name', 'N/A')}")
    print(f"Company: {user.get('company', 'N/A')}")
    print(f"Has password: {'Yes' if user.get('password_hash') else 'No'}")
    print('-' * 50)
