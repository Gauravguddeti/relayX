# Dual-Model Architecture: The Mouth & The Brain

## Overview
RelayX uses **two different AI models** for two different purposes:

### 🗣️ **The MOUTH (Groq/Llama-3.1-8b-instant)**
- **Purpose:** Real-time IVR responses during calls
- **Why:** Fast, low-latency, doesn't make users wait
- **When:** Every time the AI needs to respond during a live call
- **Model:** `llama-3.1-8b-instant` on Groq

### 🧠 **The BRAIN (Qwen/DeepSeek)**
- **Purpose:** Heavy reasoning, analysis, RAG, workflows
- **Why:** Smart, thoughtful, handles complex logic
- **When:** After calls, for knowledge base lookups, decision-making
- **Model:** `qwen-2.5-72b-instruct` or `deepseek-r1-distill-llama-70b`

---

## Why This Matters

### ❌ **What Happens If You Use Fast Model For Everything**
- Shallow responses
- Misses nuances
- Poor lead scoring
- Bad RAG results (can't reason deeply about knowledge base)
- Weak workflow decisions

### ❌ **What Happens If You Use Smart Model For Everything**
- Slow IVR responses → users hang up
- High latency → awkward pauses
- Expensive (more tokens, longer processing)

### ✅ **What Happens With Dual-Model**
- Fast, natural conversations (Groq handles talking)
- Deep, accurate analysis (Qwen handles thinking)
- Best of both worlds

---

## Architecture Flow

```
┌──────────────────────────────────────────────────────────────┐
│                        DURING CALL                           │
│                                                              │
│  User speaks → STT → Groq/Llama (FAST) → TTS → User hears  │
│                      ⚡ Real-time                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                       AFTER CALL                             │
│                                                              │
│  Transcript → Qwen/DeepSeek (SMART) → Analysis, Scoring     │
│               🧠 Heavy reasoning                             │
│                                                              │
│  → Lead score (0-100)                                        │
│  → Workflow decisions (SMS, email, etc.)                     │
│  → Strategic recommendations                                 │
│  → Pattern detection                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## What Each Model Handles

### 🗣️ **Groq/Llama (MOUTH)**

**Real-time conversation:**
- Greeting ("Hi, this is Alex from RelayX")
- Answering questions during call
- Handling objections
- Following script/prompt
- Ending call naturally

**Characteristics:**
- Response time: ~200-500ms
- Max tokens: 150 (short, focused)
- Temperature: 0.7 (natural but consistent)

---

### 🧠 **Qwen/DeepSeek (BRAIN)**

**1. Post-Call Deep Analysis**
```python
# After every call, Qwen analyzes:
{
  "lead_score": 85,  # 0-100 quality score
  "user_intent": "Looking for automation, budget-conscious",
  "conversation_quality_score": 78,
  "missed_opportunities": ["Didn't mention free trial"],
  "strategic_recommendation": "Follow up with pricing comparison",
  "follow_up_timing": "24-48 hours",
  "patterns_detected": ["Common objection: cost"]
}
```

**2. RAG Processing (Knowledge Base)**
```python
# User asks: "What are your pricing tiers?"
# Instead of Groq guessing, Qwen:

1. Searches knowledge base
2. Scores relevance of each doc
3. Detects conflicting info
4. Synthesizes accurate answer
5. Returns structured response with sources
```

**3. Workflow Decision Making**
```python
# Qwen decides based on call:
workflows = [
  "send_sms",           # Send follow-up SMS
  "schedule_callback",  # Book callback
  "update_crm"          # Update lead score
]
```

**4. Dynamic Prompt Generation**
```python
# Qwen writes intelligent prompts for Groq based on:
- Time of day (busy hours → be concise)
- Recent call patterns (common objections → address upfront)
- User history (returning caller → personalize)
- Call context (hot lead vs cold call)

# Qwen generates smart prompt → Groq executes it fast
```

**5. Lead Scoring**
```python
# Qwen evaluates BANT criteria:
- Budget: Can they afford it?
- Authority: Are they decision maker?
- Need: How urgent is their pain?
- Timeline: When do they need it?

# Returns: 0-100 score
```

**Characteristics:**
- Response time: 1-3 seconds (doesn't matter, it's async)
- Max tokens: 500-800 (detailed analysis)
- Temperature: 0.2-0.4 (precise, analytical)

---

## Code Implementation

### File: `shared/llm_client.py`
```python
class LLMClient:
    def __init__(self, use_reasoning_model: bool = False):
        if use_reasoning_model:
            # BRAIN: Qwen/DeepSeek
            self.model = "qwen-2.5-72b-instruct"
        else:
            # MOUTH: Groq/Llama
            self.model = "llama-3.1-8b-instant"
```

### File: `shared/reasoning_engine.py`
```python
class ReasoningEngine:
    """Heavy reasoning using Qwen/DeepSeek"""
    
    def __init__(self):
        self.reasoning_llm = LLMClient(use_reasoning_model=True)
    
    async def deep_call_analysis(...)
    async def rag_knowledge_search(...)
    async def workflow_decision(...)
    async def lead_scoring(...)
```

### File: `voice_gateway/voice_gateway.py`
```python
# DURING CALL: Use fast model
llm = LLMClient(use_reasoning_model=False)  # Groq/Llama
response = await llm.generate_response(...)

# AFTER CALL: Use reasoning model
reasoning_engine = ReasoningEngine()  # Qwen/DeepSeek
analysis = await reasoning_engine.deep_call_analysis(...)
```

---

## Configuration

### `.env` file:
```bash
# Fast IVR model (The MOUTH)
GROQ_MODEL=llama-3.1-8b-instant

# Reasoning model (The BRAIN)
REASONING_MODEL=qwen-2.5-72b-instruct
# or: deepseek-r1-distill-llama-70b
# or: llama-3.3-70b-versatile
```

---

## Real-World Example

### Scenario: User calls about pricing

**Step 1: During Call (MOUTH)**
```
User: "What's your pricing?"
Groq/Llama: "We have three tiers: ₹999, ₹3999, and ₹9999 per month. 
             Which one interests you?"
⚡ Response time: 300ms
```

**Step 2: After Call (BRAIN)**
```python
# Qwen analyzes transcript:
{
  "lead_score": 72,
  "user_intent": "Price shopping, budget-conscious",
  "next_action": "Send pricing comparison PDF",
  "workflow_triggers": ["send_email", "schedule_callback"],
  "pattern": "User asked about pricing in first 30 seconds → hot lead"
}

# Qwen decides workflows:
- Send email with detailed pricing breakdown
- Schedule callback in 48 hours if no response
- Update CRM with lead score 72/100
```

---

## Benefits

### Speed + Intelligence
- **Calls feel natural** (no awkward pauses)
- **Analysis is accurate** (deep reasoning post-call)

### Cost Efficiency
- **Groq is cheap/free** for high-volume calls
- **Qwen only runs once per call** (not per message)

### Scalability
- Groq handles 1000s of concurrent calls
- Qwen processes analysis queue async

### Better Outcomes
- **Higher conversion** (smart follow-up decisions)
- **Better lead scoring** (accurate prioritization)
- **Smarter RAG** (knowledge base actually helps)

---

## Analogy

Think of a high-end restaurant:

- **Waiters (MOUTH):** Fast, friendly, take orders quickly, answer basic questions
- **Chef (BRAIN):** In the kitchen, taking time to create perfect dishes, thinking about presentation, flavors, timing

You don't want the chef talking to every customer (too slow).
You don't want the waiter cooking food (not skilled enough).

Same with AI:
- **Groq** is the waiter (talks fast)
- **Qwen** is the chef (thinks deeply)

---

## Next Steps

1. ✅ Dual-model architecture implemented
2. ✅ Reasoning engine created
3. ✅ Post-call analysis integrated
4. 🚧 RAG integration (use Qwen for KB searches)
5. 🚧 Workflow automation (SMS, email triggers)
6. 🚧 Dynamic prompt generation (Qwen writes, Groq executes)

---

## Summary

| Feature | Groq/Llama (MOUTH) | Qwen/DeepSeek (BRAIN) |
|---------|-------------------|----------------------|
| **Speed** | 200-500ms | 1-3 seconds |
| **Purpose** | Talk to users | Think about data |
| **When** | During call | After call |
| **Output** | Conversational | Analytical |
| **Tokens** | 150 max | 500-800 max |
| **Cost** | Low/Free | Moderate |

**The mouth talks. The brain thinks. Together, they're unstoppable.**
