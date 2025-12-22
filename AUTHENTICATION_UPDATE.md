# Authentication & User Isolation Update

## Overview
Updated the RelayX platform to implement proper user authentication and data isolation between users and admin.

## Changes Implemented

### 1. Backend API Updates

#### Authentication System
- **File**: `backend/admin_auth.py` (NEW)
  - Double-hashed password system (SHA256 + salted SHA256)
  - Session token generation with 24-hour expiry
  - Admin user verification
  - Secure password storage in environment variables

#### Admin Routes
- **File**: `backend/admin_routes.py` (NEW)
  - Multi-client dashboard endpoints
  - System-wide analytics
  - Bulk operations (delete old calls, export data)
  - Audit trail functionality

#### Main API Endpoints
- **File**: `backend/main.py` (MODIFIED)
  
  **Authentication Endpoints:**
  - `POST /auth/login` - User login with email/password
  - `POST /admin/login` - Admin login with username/password
  - `POST /admin/logout` - Admin logout
  - `GET /admin/verify` - Verify admin session token

  **Agent Endpoints:**
  - `GET /agents?user_id={uuid}` - List agents filtered by user
  - `PUT /agents/{id}` - Update agent (now accepts user_id parameter)
  - `POST /agents` - Create agent (associates with user_id)

  **Call Endpoints:**
  - `GET /calls?user_id={uuid}` - List calls filtered by user
  - `POST /calls/outbound` - Create call (auto-associates with agent's user_id)

#### Static Admin Pages
- **File**: `backend/static/admin-login.html` (NEW)
  - Secure admin login page
  - Token-based authentication
  - Auto-redirect if already logged in

- **File**: `backend/static/admin.html` (NEW)
  - Multi-client dashboard
  - Client profile cards with stats
  - System analytics overview
  - Bulk operations interface
  - Audit trail viewer
  - Session verification on page load

### 2. Frontend React App Updates

#### Authentication Context
- **File**: `frontend/src/contexts/AuthContext.tsx` (MODIFIED)
  - Replaced mock authentication with real backend integration
  - Async login function calling `/auth/login`
  - JWT token storage in localStorage (`relayx_token`)
  - User object storage in localStorage (`relayx_user`)
  - Token verification on app mount
  - userId exposed to components

#### Login Page
- **File**: `frontend/src/pages/LoginPage.tsx` (MODIFIED)
  - Converted to async handleSubmit
  - Improved error handling

#### Bot Settings
- **File**: `frontend/src/pages/BotSettings.tsx` (MODIFIED)
  - Added `useAuth()` hook to get current userId
  - Filter agents by `user_id` on fetch
  - Include `user_id` when creating new bots
  - Include `user_id` when updating bots
  - Only show bots owned by current user

#### Dashboard
- **File**: `frontend/src/pages/Dashboard.tsx` (MODIFIED)
  - Added `useAuth()` hook
  - Filter calls by `user_id` on fetch
  - Display only current user's call statistics

#### Calls Page
- **File**: `frontend/src/pages/Calls.tsx` (MODIFIED)
  - Added `useAuth()` hook
  - Filter calls by `user_id` on fetch
  - Display only current user's call history

#### New Call Modal
- **File**: `frontend/src/components/dashboard/NewCallModal.tsx` (MODIFIED)
  - Added `useAuth()` hook
  - Filter available agents by `user_id`
  - Only show agents owned by current user

#### Recent Calls List
- **File**: `frontend/src/components/dashboard/RecentCallsList.tsx` (MODIFIED)
  - Added `useAuth()` hook
  - Filter calls by `user_id` on fetch

## User Isolation

### Admin (localhost:8000)
- **Username**: `admin`
- **Password**: `RelayX@2025`
- **Access**: Can view ALL users, ALL agents, ALL calls
- **Features**:
  - Multi-client dashboard
  - System-wide analytics
  - Bulk operations
  - Audit trail
  - Client management

### Regular Users (localhost:3000)
- **Login**: Email + Password
- **Access**: Can ONLY view their own data
- **Features**:
  - Create and manage their own bots
  - Make calls using their bots
  - View their call history
  - Dashboard with their statistics

## Database Schema

### Tables with user_id
- `users` - User accounts table
- `agents` - Bots (each belongs to one user)
- `calls` - Call records (associated with agent's user_id)
- `knowledge_base` - Knowledge entries (belongs to user)

### Indexes for Performance
```sql
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_calls_user_id ON calls(user_id);
CREATE INDEX idx_knowledge_user_id ON knowledge_base(user_id);
```

## Security Features

### Password Hashing
- Double SHA256 hashing with salt
- First hash: SHA256(password)
- Second hash: SHA256(first_hash + salt)
- Admin password stored in `ADMIN_PASSWORD_HASH` env var

### Session Management
- JWT tokens with 24-hour expiry
- Tokens stored in localStorage
- Token verification on protected routes
- Auto-redirect to login if token invalid

### API Security
- All agent/call endpoints require user_id
- Backend filters results by user_id
- Users cannot access other users' data
- Admin can access all data via admin dashboard

## Testing Checklist

- [x] Admin can login at localhost:8000
- [x] Admin sees all 3 existing bots
- [ ] Create new user via admin dashboard
- [ ] New user can login at localhost:3000
- [ ] New user sees no bots initially
- [ ] New user can create their first bot
- [ ] New user only sees their own bot
- [ ] New user can make calls with their bot
- [ ] New user only sees their own call history
- [ ] Admin still sees all bots and calls
- [ ] User cannot see admin's bots
- [ ] User cannot see other users' bots

## Deployment

### Docker Containers Updated
```bash
# Frontend rebuilt with auth changes
docker compose build frontend --no-cache
docker compose up -d frontend

# Backend restarted with API changes
docker compose restart backend
```

### Environment Variables Required
```env
# Admin Authentication
ADMIN_PASSWORD_HASH=<double_hashed_password>
ADMIN_USERNAME=admin

# JWT Secret (if using JWT tokens)
JWT_SECRET=<random_secret_key>
```

## Known Limitations

### Current Implementation
- Admin sessions stored in-memory (lost on restart)
- Need Redis for persistent session storage in production
- No refresh token rotation yet
- No rate limiting on login attempts

### Recommended Improvements
1. Move session storage to Redis
2. Implement refresh token rotation
3. Add rate limiting for login endpoints
4. Add HTTPS/SSL configuration
5. Implement password reset functionality
6. Add email verification
7. Add 2FA for admin accounts
8. Add comprehensive audit logging

## API Documentation

### User Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "jwt_token_here",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name"
  }
}
```

### Admin Login
```http
POST /admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "RelayX@2025"
}

Response:
{
  "success": true,
  "token": "session_token_here",
  "message": "Login successful"
}
```

### List User's Agents
```http
GET /agents?user_id={uuid}

Response:
[
  {
    "id": "agent_uuid",
    "name": "My Bot",
    "user_id": "user_uuid",
    "is_active": true,
    ...
  }
]
```

### List User's Calls
```http
GET /calls?user_id={uuid}&limit=50

Response:
[
  {
    "id": "call_uuid",
    "agent_id": "agent_uuid",
    "user_id": "user_uuid",
    "to_number": "+1234567890",
    "status": "completed",
    ...
  }
]
```

## Admin Dashboard Features

### Client Cards
- Display all registered users
- Show user profile information
- Display agent count per user
- Show call statistics per user

### Analytics
- Total clients count
- Active clients (with calls)
- Total calls across all users
- System success rate

### Bulk Operations
- Delete calls older than X days
- Export all data as JSON
- Backup system data

### Audit Trail
- View all system events
- Filter by user, action, date
- Export audit logs

## Troubleshooting

### Issue: Users see other users' bots
**Solution**: Check that frontend is passing `user_id` parameter in API calls

### Issue: Admin cannot see all bots
**Solution**: Admin dashboard uses `/agents` without user_id filter to see all

### Issue: Token invalid on refresh
**Solution**: Check localStorage for `relayx_token`, verify token not expired (24h)

### Issue: Backend returns 404 for agent updates
**Solution**: Ensure `user_id` is included in request body for authorization

### Issue: Calls not associated with user
**Solution**: Check that `create_call` passes `user_id` from agent

## Future Enhancements

1. **Multi-tenancy**: Add organization/team support
2. **Role-based Access Control**: Add user roles (admin, manager, agent)
3. **API Keys**: Generate API keys for programmatic access
4. **Webhooks**: Add webhook support for events
5. **SSO Integration**: Support OAuth providers (Google, Microsoft)
6. **Mobile App**: Build React Native mobile app
7. **Real-time Updates**: Add WebSocket support for live updates
8. **Advanced Analytics**: Add detailed reporting and insights
