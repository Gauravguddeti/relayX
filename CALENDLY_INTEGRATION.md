# Calendly Integration Guide

## Overview
RelayX now integrates with Calendly to enable seamless appointment booking directly from your AI calls. This allows your AI agent to schedule meetings with prospects in real-time.

## ✅ Configuration Completed

The following has been configured in your `.env` file:

```env
CALENDLY_API_TOKEN=eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ...
CALENDLY_EVENT_TYPE_URL=https://calendly.com/universalviewer69/30min
```

## 🎯 Features

### 1. **Personalized Scheduling Links**
- Create pre-filled Calendly links with prospect information
- Automatically includes name, email, phone, and notes
- Perfect for sharing during or after calls

### 2. **SMS Integration**
- Send scheduling links directly via SMS using Twilio
- Instant delivery to prospect's phone
- Pre-filled with their information for quick booking

### 3. **Available Time Slots**
- Query available times from your Calendly calendar
- Check availability for the next 30 days
- Helps AI agent suggest specific times

### 4. **Direct Scheduling** (if permissions allow)
- Book appointments directly through API
- No need for prospect to visit Calendly page
- Instant confirmation

## 🚀 Usage

### Via Dashboard
1. Navigate to **Dashboard → Calendly** in the sidebar
2. Enter prospect details (name, email, phone)
3. Click **Generate Link** to create a personalized booking URL
4. Click **Send via SMS** to text the link directly to the prospect

### Via API

#### Check Integration Status
```bash
GET /calendly/status
```

#### Create Scheduling Link
```bash
POST /calendly/create-link
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "notes": "Demo request"
}
```

#### Send Link via SMS
```bash
POST /calendly/send-link-sms
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890"
}
```

#### Get Available Times
```bash
GET /calendly/available-times?start_date=2024-01-15&end_date=2024-01-30
```

#### Schedule Event Directly
```bash
POST /calendly/schedule-event
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "start_time": "2024-01-15T10:00:00Z",
  "phone": "+1234567890",
  "notes": "Demo call"
}
```

## 🤖 AI Agent Integration

You can add Calendly booking to your AI agent's capabilities by updating the system prompt:

```
When a prospect is interested in scheduling a meeting:

1. Collect their name, email, and phone number
2. Offer to send them a booking link via SMS
3. Use the /calendly/send-link-sms API to send the link
4. Confirm that the SMS was sent

Example: "Great! I'd love to schedule a demo with you. Can I have your email and phone number? I'll text you a link where you can pick a time that works best for you."
```

## 📝 Best Practices

### 1. **Pre-Qualification**
- Only offer scheduling after confirming interest
- Collect all necessary information first
- Explain what the meeting will cover

### 2. **SMS Delivery**
- Always confirm phone number format (+1234567890)
- Send during business hours when possible
- Include context in the notes field

### 3. **Follow-Up**
- Track who received links in your CRM
- Send reminder emails before meetings
- Use Calendly's built-in reminder features

### 4. **Personalization**
- Include relevant notes about the conversation
- Pre-fill as much info as possible
- Reference specific topics discussed

## 🔧 Implementation Files

- **Backend**: `backend/calendly_routes.py` - API endpoints
- **Shared**: `shared/calendly_client.py` - Calendly API client
- **Frontend**: `frontend/src/pages/CalendlyIntegration.tsx` - Dashboard UI
- **Config**: `.env` - API credentials

## 🔐 Security Notes

- API token is stored in `.env` (never commit to Git)
- Token uses Calendly's OAuth 2.0 authentication
- Rate limits apply (60 requests per minute)
- All API calls are logged for audit purposes

## 📊 Analytics

Track booking metrics by monitoring:
- Number of links created
- SMS delivery success rate
- Booking conversion rate
- Most popular time slots

## 🆘 Troubleshooting

### "Calendly integration not configured"
- Verify `CALENDLY_API_TOKEN` is set in `.env`
- Restart backend: `docker compose restart backend`

### SMS not sending
- Check Twilio configuration in `.env`
- Verify phone number format (+1XXXXXXXXXX)
- Check Twilio balance

### No available times showing
- Check event type URL is correct
- Verify Calendly availability settings
- Ensure event type is active

## 🎓 Next Steps

1. **Test the integration** in the dashboard
2. **Update your AI agent prompt** to offer booking
3. **Train your team** on when to offer scheduling
4. **Monitor conversion rates** and optimize

## 📖 Resources

- [Calendly API Documentation](https://developer.calendly.com/)
- [Calendly Event Types](https://calendly.com/event_types)
- [Calendly Integrations](https://calendly.com/integrations)

---

**Need Help?** Check the logs at `backend/logs/backend.log` or contact support.
