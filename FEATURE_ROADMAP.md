# RelayX Feature Roadmap & Architecture Notes

## 🚨 CRITICAL: User Data Isolation

### Current Issues to Fix
**The current backend does NOT have user authentication/isolation.** All agents, calls, and knowledge base are shared across all users.

### Required Changes for Multi-User Support

#### 1. Backend Authentication System
```python
# Add to backend/main.py
from fastapi import Depends, HTTPException, Header
from jose import JWTError, jwt

async def get_current_user(authorization: str = Header(None)):
    """Extract user from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    # Verify JWT and extract user_id
    user_id = verify_token(token)
    return user_id
```

#### 2. Database Schema Updates
```sql
-- Add users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add user_id to agents
ALTER TABLE agents ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX idx_agents_user_id ON agents(user_id);

-- Add user_id to knowledge_base
ALTER TABLE knowledge_base ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX idx_knowledge_user_id ON knowledge_base(user_id);

-- Add user_id to calls
ALTER TABLE calls ADD COLUMN user_id UUID REFERENCES users(id);
CREATE INDEX idx_calls_user_id ON calls(user_id);
```

#### 3. API Endpoint Updates
Every endpoint needs to:
- Accept JWT token in Authorization header
- Filter data by user_id
- Return only user-specific data

```python
@app.get("/agents")
async def get_agents(user_id: str = Depends(get_current_user)):
    return supabase.table("agents").select("*").eq("user_id", user_id).execute()

@app.get("/calls")
async def get_calls(user_id: str = Depends(get_current_user)):
    return supabase.table("calls").select("*").eq("user_id", user_id).execute()
```

---

## 📞 Bulk Calling Feature (Priority: High)

### Phase 1: CSV Upload & Campaign Management

#### Features to Add:
1. **CSV Import Page** (`/dashboard/campaigns`)
   - Upload CSV with columns: Name, Phone, Email, Company, Tags
   - Preview data before import
   - Validate phone numbers
   - Map CSV columns to contact fields
   - Save as campaign

2. **Campaign Management**
   ```typescript
   interface Campaign {
     id: string;
     user_id: string;
     name: string;
     description: string;
     total_contacts: number;
     completed: number;
     successful: number;
     failed: number;
     status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed';
     scheduled_at?: string;
     agent_id: string;
     created_at: string;
   }
   ```

3. **Campaign Scheduler**
   - Set call schedule (time window, days)
   - Call rate limiting (calls per minute/hour)
   - Time zone handling
   - Retry logic for failed calls

4. **Live Campaign Dashboard**
   - Real-time progress bar
   - Success/failure rates
   - Average call duration
   - Pause/Resume controls
   - Export results

#### Backend Implementation:
```python
# New endpoints needed:
POST   /campaigns                    # Create campaign
GET    /campaigns                    # List user's campaigns
GET    /campaigns/{id}               # Get campaign details
PUT    /campaigns/{id}               # Update campaign
DELETE /campaigns/{id}               # Delete campaign
POST   /campaigns/{id}/start         # Start campaign
POST   /campaigns/{id}/pause         # Pause campaign
POST   /campaigns/{id}/contacts      # Add contacts to campaign
GET    /campaigns/{id}/stats         # Get campaign statistics
POST   /campaigns/import-csv         # Import CSV file

# Background job processor (Celery/RQ)
- Process campaign queue
- Make calls with rate limiting
- Update campaign status
- Handle retries
```

### Phase 2: Advanced Features
- A/B testing (multiple bot scripts)
- Call recording transcription
- Sentiment analysis on bulk calls
- Auto-follow-up scheduling
- Integration with CRM (HubSpot, Salesforce)

---

## 🎯 Essential Features to Add

### 1. Analytics Dashboard (High Priority)
**Path:** `/dashboard/analytics`

**Metrics to Track:**
- Call success rate over time
- Average call duration
- Peak calling hours
- Conversion funnel (answered → interested → booked)
- Cost per call
- Bot performance score
- Common objections/questions
- Geographic distribution

**Visualizations:**
- Line charts (calls over time)
- Pie charts (outcomes distribution)
- Heat maps (best calling times)
- Funnel charts (conversion stages)

### 2. Call Scripts & Templates (High Priority)
**Path:** `/dashboard/scripts`

**Features:**
- Pre-built templates by industry:
  - Medical appointment confirmation
  - Real estate lead qualification
  - Restaurant reservations
  - Sales follow-up
  - Survey calls
  - Event invitations

- Script builder with:
  - Branching logic (if interested → ask X, if not → ask Y)
  - Variable insertion {contact.name}, {contact.company}
  - Objection handling templates
  - Call-to-action options

### 3. Call Recording Library (Medium Priority)
**Path:** `/dashboard/recordings`

**Features:**
- Search recordings by date, contact, outcome
- Playback with transcript sync
- Bookmark important moments
- Share specific calls with team
- Add notes to recordings
- Download recordings

### 4. Appointment Scheduling (High Priority)
**Path:** `/dashboard/calendar`

**Features:**
- Calendar integration (Google Calendar, Outlook)
- Available time slots configuration
- Auto-book appointments from calls
- Send confirmation emails/SMS
- Reminder system
- Reschedule/cancel handling

### 5. Team Collaboration (Medium Priority)
**Path:** `/dashboard/team`

**Features:**
- Invite team members
- Role-based permissions (Admin, Manager, Agent, Viewer)
- Shared campaigns
- Comments on calls
- Team performance leaderboard
- Call assignment

### 6. Notifications & Alerts (High Priority)
**Features:**
- Real-time notifications for:
  - Call completed
  - Lead interested
  - Appointment booked
  - Campaign finished
  - Bot error/issue
- Notification channels:
  - Email
  - SMS
  - Slack webhook
  - Discord webhook
  - Push notifications

### 7. Integrations Hub (Medium Priority)
**Path:** `/dashboard/integrations`

**Integrations to Add:**
- **CRM:** HubSpot, Salesforce, Pipedrive
- **Calendar:** Google Calendar, Outlook, Calendly
- **Communication:** Slack, Discord, Telegram
- **Zapier** - Connect to 5000+ apps
- **Webhooks** - Custom integrations

### 8. Billing & Usage (High Priority)
**Path:** `/dashboard/billing`

**Features:**
- Usage dashboard (minutes used, calls made)
- Pricing plans (Starter, Pro, Enterprise)
- Payment method management (Stripe)
- Invoice history
- Usage alerts (80% quota, over limit)
- Upgrade/downgrade flow

### 9. AI Training & Optimization (High Priority)
**Path:** `/dashboard/training`

**Features:**
- Review flagged calls (bot made mistake)
- Provide feedback to improve responses
- Add custom vocabulary/jargon
- Train on successful call patterns
- Test changes in sandbox before deploying
- Version history of bot configurations

### 10. Compliance & Security (Critical)
**Path:** `/dashboard/compliance`

**Features:**
- TCPA compliance checker
- Do Not Call (DNC) list integration
- Call consent recording
- Data retention policies
- GDPR/CCPA compliance tools
- Audit logs (who accessed what)
- Data export (user data portability)

---

## 🔧 Technical Improvements Needed

### Security
```typescript
// 1. JWT Authentication in Frontend
const authApi = {
  login: async (email: string, password: string) => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const { access_token, refresh_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    return access_token;
  },
  
  refreshToken: async () => {
    const refresh = localStorage.getItem('refresh_token');
    const res = await fetch('/auth/refresh', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refresh}`
      }
    });
    const { access_token } = await res.json();
    localStorage.setItem('access_token', access_token);
    return access_token;
  }
};

// 2. API Client with Auto-Retry
class ApiClient {
  async fetch(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
      },
    });

    // Auto-refresh on 401
    if (response.status === 401) {
      await authApi.refreshToken();
      return this.fetch(url, options); // Retry
    }

    return response;
  }
}
```

### Database Optimization
```sql
-- Indexes for performance
CREATE INDEX idx_calls_created_at ON calls(created_at DESC);
CREATE INDEX idx_calls_user_status ON calls(user_id, status);
CREATE INDEX idx_agents_user_active ON agents(user_id, is_active);

-- Partitioning for scale (calls table gets huge)
CREATE TABLE calls_2025_01 PARTITION OF calls
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### Caching Strategy
```python
# Redis caching for frequently accessed data
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379)

@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user_id: str = Depends(get_current_user)):
    # Check cache first
    cache_key = f"agent:{user_id}:{agent_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Fetch from DB
    agent = supabase.table("agents").select("*").eq("id", agent_id).eq("user_id", user_id).single().execute()
    
    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(agent.data))
    return agent.data
```

---

## 📊 Immediate Next Steps (Priority Order)

1. **[CRITICAL] Add User Authentication**
   - Backend: JWT auth, user table, user_id filtering
   - Frontend: Real login/signup (not test credentials)
   - Migrate existing data to have user associations

2. **[HIGH] Bulk Calling - Phase 1**
   - CSV upload page
   - Campaign table/management
   - Queue processor for bulk calls

3. **[HIGH] Analytics Dashboard**
   - Call statistics over time
   - Outcome tracking
   - Performance metrics

4. **[HIGH] Appointment Scheduler**
   - Calendar integration
   - Auto-booking from calls

5. **[MEDIUM] Call Scripts Library**
   - Industry templates
   - Script customization

6. **[MEDIUM] Billing System**
   - Usage tracking
   - Payment integration (Stripe)
   - Plan management

---

## 💡 UI/UX Enhancements

### Dashboard Improvements
- Add charts/graphs for statistics (use Chart.js or Recharts)
- Real-time call status updates (WebSocket)
- Quick action buttons (New Campaign, New Call, Add Contact)
- Recent activity feed
- Keyboard shortcuts

### Mobile Responsiveness
- Currently desktop-only
- Add mobile navigation (hamburger menu)
- Touch-friendly buttons
- Mobile-optimized tables (cards on mobile)

### Dark Mode
- Add theme toggle
- Save preference in localStorage
- CSS variables for colors

### Onboarding Flow
- First-time user tutorial
- Interactive demo call
- Bot setup wizard
- Sample data to explore

---

## 🚀 Scalability Considerations

### For 1000+ Users
- Load balancer (Nginx/HAProxy)
- Horizontal scaling (multiple backend instances)
- Database read replicas
- CDN for frontend assets

### For 10,000+ Concurrent Calls
- Microservices architecture
  - Auth service
  - Call service
  - Campaign service
  - Analytics service
- Message queue (RabbitMQ/Kafka) for call processing
- Distributed tracing (OpenTelemetry)
- Auto-scaling based on load

### Cost Optimization
- Voice provider negotiation (volume discounts)
- Efficient call routing
- Call recording compression
- Database query optimization
- Cache frequently accessed data

---

## 📝 Documentation Needed

1. **API Documentation** (Swagger/OpenAPI)
2. **User Guide** (How to use each feature)
3. **Developer Guide** (How to contribute)
4. **Deployment Guide** (Production setup)
5. **Security Best Practices**
6. **Compliance Guide** (TCPA, GDPR)

---

## 🎨 Design System

Create a consistent design language:
- Color palette (primary, secondary, success, error, etc.)
- Typography scale
- Spacing system (4px grid)
- Component library (buttons, inputs, cards, etc.)
- Icon set (Lucide Icons - already using)
- Animation guidelines

---

This roadmap provides a clear path from MVP to enterprise-grade product. Focus on user authentication and data isolation first, then bulk calling, then everything else!
