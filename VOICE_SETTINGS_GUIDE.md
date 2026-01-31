# 🎙️ Voice Settings & Pipeline Configuration Guide

## Overview

RelayX now supports **per-agent voice configuration** allowing fine-tuned control over voice activity detection (VAD), silence thresholds, audio processing, and speech detection parameters. Each agent can have customized voice settings optimized for different call scenarios.

## Features

### ✅ What's New

- **Per-Agent Voice Settings**: Each agent can have unique voice configuration
- **Voice Presets**: Pre-configured settings for common scenarios
- **Custom Tuning**: Granular control over all voice pipeline parameters
- **Real-time Application**: Settings applied immediately when call starts
- **Persistent Storage**: Settings saved in database and loaded automatically

---

## UI Configuration

### Accessing Voice Settings

1. Go to **Agent Settings** in the dashboard
2. Create a new agent or edit an existing one
3. Scroll to **🎙️ Voice & Audio Settings** section
4. Click to expand the collapsible panel

### Voice Presets

Choose from 5 pre-configured presets optimized for different scenarios:

#### ⚖️ Balanced (Recommended)
- **Best for**: Most call scenarios with good quality
- **VAD Mode**: 2 (Moderate)
- **Silence Threshold**: 600ms
- **Use when**: General purpose calling with mixed quality

#### ⚡ Fast & Responsive
- **Best for**: Clean connections, quick interactions
- **VAD Mode**: 1 (Less aggressive)
- **Silence Threshold**: 500ms
- **Use when**: High-quality VoIP, office environment

#### 🛡️ Conservative
- **Best for**: Noisy environments, prevent false triggers
- **VAD Mode**: 3 (Very aggressive)
- **Silence Threshold**: 800ms
- **Use when**: Background noise, public spaces, poor line quality

#### 📱 Mobile Optimized
- **Best for**: Cellular connections with variable quality
- **VAD Mode**: 2 (Moderate)
- **Silence Threshold**: 700ms
- **Use when**: Mobile phones, varying network conditions

#### 🎛️ Custom
- **Best for**: Advanced users who want full control
- **Allows**: Manual adjustment of all parameters
- **Use when**: Specific requirements, testing, optimization

---

## Voice Settings Parameters

### 1. VAD Mode (Voice Activity Detection)

**Range**: 0-3  
**Default**: 2

Controls how aggressively the system filters out non-speech:

- **0 - Quality**: Captures all speech, may include background noise
- **1 - Low Bitrate**: Mildly aggressive filtering
- **2 - Aggressive**: Balanced filtering (recommended)
- **3 - Very Aggressive**: Heavy filtering, may cut off soft speech

**When to adjust**:
- Increase (2→3) if detecting too much background noise
- Decrease (2→1) if cutting off user's speech

---

### 2. Silence Threshold

**Range**: 300-1200ms  
**Default**: 600ms

Duration of silence after user stops speaking before processing begins.

**Impact**:
- **Lower (500ms)**: Faster response, may cut off slow speakers
- **Higher (800ms)**: More accurate, slight delay in response

**When to adjust**:
- Decrease for fast-paced conversations
- Increase for users who pause frequently while speaking

---

### 3. Minimum Audio Duration

**Range**: 200-800ms  
**Default**: 400ms

Minimum speech duration required to trigger processing.

**Impact**:
- **Lower (300ms)**: Process shorter utterances, may include noise
- **Higher (500ms)**: Filter out short noises, may miss quick responses

**When to adjust**:
- Increase if processing random noises or echoes
- Decrease if missing quick "yes/no" responses

---

### 4. Minimum Speech Energy

**Range**: 10-80  
**Default**: 30

Energy threshold to distinguish speech from silence/noise.

**Impact**:
- **Lower (20)**: Detect quiet speech, may include background noise
- **Higher (40)**: Filter noise better, may miss soft speakers

**When to adjust**:
- Increase for noisy environments
- Decrease for quiet speakers or poor microphones

---

### 5. Echo Ignore Window

**Range**: 200-800ms  
**Default**: 400ms

Duration to ignore incoming audio after AI finishes speaking (prevents echo detection).

**Impact**:
- **Lower (300ms)**: Faster barge-in, risk of false echo detection
- **Higher (500ms)**: Better echo protection, slight delay in barge-in

**When to adjust**:
- Increase if AI's speech is being detected as user input
- Decrease if legitimate interruptions are being ignored

---

### 6. Speech Start Threshold

**Range**: 100-500ms  
**Default**: 200ms

Continuous speech duration needed to trigger speech detection.

**Impact**:
- **Lower (150ms)**: More responsive, may trigger on noise
- **Higher (250ms)**: More accurate, slight delay in detection

**When to adjust**:
- Increase if false triggers from background sounds
- Decrease for very responsive interactions

---

### 7. Speech End Threshold

**Range**: 100-500ms  
**Default**: 240ms

Silence duration needed to mark speech as ended.

**Impact**:
- **Lower (200ms)**: Faster processing, may cut off mid-sentence
- **Higher (300ms)**: Better handling of pauses, slower processing

**When to adjust**:
- Increase if cutting off users mid-sentence
- Decrease for faster turn-taking

---

## Technical Implementation

### Database Schema

Voice settings are stored in the `agents` table:

```sql
voice_settings JSONB DEFAULT '{}'
```

Example stored structure:
```json
{
  "vad_mode": 2,
  "silence_threshold_ms": 600,
  "min_audio_duration_ms": 400,
  "min_speech_energy": 30,
  "echo_ignore_ms": 400,
  "speech_start_ms": 200,
  "speech_end_ms": 240,
  "preset": "balanced"
}
```

### Frontend Implementation

**Location**: `frontend/src/pages/AgentSettings.tsx`

**Key Features**:
- Collapsible voice settings section
- Preset selection with visual cards
- Custom slider controls for advanced users
- Real-time settings summary
- Settings persisted on agent save

**State Management**:
```typescript
const [voiceSettingsPreset, setVoiceSettingsPreset] = useState('balanced');
const [vadMode, setVadMode] = useState(2);
const [silenceThreshold, setSilenceThreshold] = useState(600);
// ... other settings
```

### Backend/Voice Gateway Integration

**Location**: `voice_gateway/voice_gateway.py`

**CallSession Initialization**:
```python
def __init__(self, call_id: str, agent_id: str, stream_sid: str, voice_settings: dict = None):
    # Apply custom settings or use defaults
    if voice_settings:
        self.SPEECH_START_MS = voice_settings.get('speech_start_ms', 200)
        self.MIN_STT_DURATION_MS = voice_settings.get('silence_threshold_ms', 500)
        # ... apply other settings
```

**Runtime Application**:
- Settings loaded from agent config when WebSocket connects
- Passed to `CallSession` constructor
- Applied immediately for that specific call
- Each call session can have different settings

---

## Best Practices

### 1. Start with Presets
- Use **Balanced** preset for most cases
- Test call quality before customizing
- Only switch to Custom if presets don't work

### 2. Tune Incrementally
- Change one parameter at a time
- Test thoroughly after each change
- Document what works for your use case

### 3. Consider Call Quality
- **Clean VoIP**: Use Fast & Responsive
- **Mobile/Cellular**: Use Mobile Optimized
- **Noisy Background**: Use Conservative
- **Unknown**: Start with Balanced

### 4. Monitor Performance
- Check voice gateway logs for VAD metrics
- Watch for "noise detected" vs "processing speech"
- Adjust based on false positives/negatives

### 5. Environment-Specific Settings
- Create different agents for different scenarios
- Office hours agent: Fast & Responsive
- After-hours agent: Conservative (background noise)
- Mobile outreach: Mobile Optimized

---

## Troubleshooting

### Problem: Agent cuts off user mid-sentence

**Solution**:
1. Increase **Silence Threshold** (600ms → 800ms)
2. Increase **Speech End Threshold** (240ms → 300ms)
3. Consider using **Conservative** preset

### Problem: Agent is too slow to respond

**Solution**:
1. Decrease **Silence Threshold** (600ms → 500ms)
2. Decrease **Speech Start Threshold** (200ms → 150ms)
3. Consider using **Fast & Responsive** preset

### Problem: Background noise triggers false responses

**Solution**:
1. Increase **VAD Mode** (2 → 3)
2. Increase **Min Speech Energy** (30 → 40)
3. Increase **Min Audio Duration** (400ms → 500ms)
4. Consider using **Conservative** preset

### Problem: AI's speech triggers echo detection

**Solution**:
1. Increase **Echo Ignore Window** (400ms → 500ms)
2. Check Twilio echo cancellation settings
3. Verify audio routing (prevent feedback loops)

### Problem: Quick responses like "yes" are missed

**Solution**:
1. Decrease **Min Audio Duration** (400ms → 300ms)
2. Decrease **VAD Mode** (2 → 1)
3. Ensure **Min Speech Energy** isn't too high

---

## API Reference

### Creating Agent with Voice Settings

```javascript
POST /agents
{
  "name": "Sales Agent",
  "prompt_text": "...",
  "voice_settings": {
    "vad_mode": 2,
    "silence_threshold_ms": 600,
    "min_audio_duration_ms": 400,
    "min_speech_energy": 30,
    "echo_ignore_ms": 400,
    "speech_start_ms": 200,
    "speech_end_ms": 240,
    "preset": "balanced"
  }
}
```

### Updating Voice Settings

```javascript
PUT /agents/{agent_id}
{
  "voice_settings": {
    "preset": "fast",
    "vad_mode": 1,
    "silence_threshold_ms": 500
    // ... other settings
  }
}
```

---

## Performance Impact

### Latency Considerations

| Setting | Lower Value | Higher Value |
|---------|-------------|--------------|
| Silence Threshold | Faster response | More accurate |
| Min Audio Duration | More responsive | Better filtering |
| Speech Start | Quicker detection | Fewer false triggers |
| Speech End | Faster turn-taking | Better pause handling |

### Quality vs Speed Trade-off

- **Speed Priority**: Use Fast & Responsive preset
  - Target: <2s response time
  - Risk: May cut off slow speakers

- **Quality Priority**: Use Conservative preset
  - Target: <4s response time
  - Benefit: Better accuracy, fewer errors

- **Balanced**: Use Balanced/Mobile presets
  - Target: <3s response time
  - Benefit: Good mix of speed and accuracy

---

## Testing & Validation

### 1. Test Different Scenarios
- Clean environment (office)
- Noisy environment (street, cafe)
- Mobile phone connection
- VoIP/landline connection

### 2. Monitor Metrics
Watch logs for:
```
📊 Buffer: 16000B | Silence: 450ms | Speech: 85% | IsSilence: False
🚫 Energy too low (25.3 < 30) - skipping
✅ Processing audio: 1.2s duration
```

### 3. User Feedback
- Are responses too fast/slow?
- Is agent cutting off user?
- Are there false triggers?
- Is speech detection reliable?

---

## Migration Guide

### Existing Agents

All existing agents without voice_settings will use default values (Balanced preset). To customize:

1. Edit the agent in Agent Settings
2. Expand Voice & Audio Settings
3. Select appropriate preset or customize
4. Save agent

Settings will apply to all new calls using that agent.

---

## Future Enhancements

Planned features:
- [ ] A/B testing different presets
- [ ] Real-time voice settings adjustment during calls
- [ ] Analytics dashboard for voice quality metrics
- [ ] Auto-optimization based on call success rates
- [ ] Voice setting recommendations based on use case
- [ ] Additional TTS voice options
- [ ] Language-specific optimizations

---

## Support

For questions or issues with voice settings:

1. Check logs in `voice_gateway/logs/`
2. Review [WEBRTCVAD_INTEGRATION.md](WEBRTCVAD_INTEGRATION.md)
3. Check [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)
4. Contact support with specific call IDs for analysis

---

**Last Updated**: December 27, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
