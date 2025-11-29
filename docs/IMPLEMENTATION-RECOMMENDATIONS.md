# Implementation Recommendations for Mobile Compatibility

## Priority Order

1. **HIGH** - Add iOS AudioContext warmup script
2. **HIGH** - Update SDK import to new package
3. **MEDIUM** - Add mobile-specific UI/UX improvements
4. **LOW** - Add audio routing fix for headphones

---

## 1. Add iOS AudioContext Warmup (HIGH PRIORITY)

Add this script to `index.html` in the `<head>` section, BEFORE any other scripts:

```html
<head>
    <!-- ... other head content ... -->

    <!-- iOS Safari Audio Fix - MUST be first -->
    <script>
    (function() {
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!window.AudioContext) return;

        window.audioContext = new window.AudioContext();
        var unlocked = false;

        function unlock(e) {
            if (unlocked) return;
            var buffer = window.audioContext.createBuffer(1, 1, 22050);
            var source = window.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(window.audioContext.destination);
            source.start ? source.start(0) : source.noteOn(0);

            window.audioContext.resume().then(function() {
                unlocked = true;
                console.log('[iOS Fix] Audio unlocked');
            }).catch(function() {});
        }

        ['touchstart','touchend','click','keydown'].forEach(function(e) {
            document.addEventListener(e, unlock, {passive:true, once:false});
        });
    })();
    </script>

    <!-- Then Clerk script -->
    <script async crossorigin="anonymous" ...></script>
</head>
```

---

## 2. Update SDK Import (HIGH PRIORITY)

The `@11labs/client` package is deprecated. Update to the new package:

```javascript
// OLD (current - deprecated)
import { Conversation } from 'https://cdn.jsdelivr.net/npm/@11labs/client@latest/+esm';

// NEW (recommended)
import { Conversation } from 'https://cdn.jsdelivr.net/npm/@elevenlabs/client@latest/+esm';
```

---

## 3. Improve toggleConversation for Mobile (HIGH PRIORITY)

Replace the current `toggleConversation` function with this improved version:

```javascript
window.toggleConversation = async function() {
    if (!agentId) {
        setupModal.classList.remove('hidden');
        return;
    }

    // Prevent multiple instances
    if (isConnecting) {
        console.log('Already connecting, ignoring');
        return;
    }

    if (conversation) {
        // End conversation
        await conversation.endSession();
        conversation = null;
        callButton.classList.remove('active', 'connecting');
        callIcon.textContent = '📞';
        updateStatus('disconnected', 'OFFLINE');
        isSpeaking = false;
        targetAmplitude = 0;
        setMood('neutral');
        hideTranscription();
    } else {
        // Check if user is logged in
        if (!clerkUser) {
            showError('Please login to talk to Pi-Guy');
            document.getElementById('login-btn')?.click();
            return;
        }

        // Check usage limit
        try {
            const usageResp = await fetch(`${VISION_SERVER_URL}/api/usage/${clerkUser.id}`);
            const usage = await usageResp.json();
            if (!usage.allowed) {
                showError(`Monthly limit reached (${usage.limit} responses). Try again next month!`);
                return;
            }
        } catch (e) {
            console.error('Usage check failed:', e);
        }

        // Start conversation
        isConnecting = true;
        callButton.classList.add('connecting');
        callIcon.textContent = '⏳';
        updateStatus('connecting', 'CONNECTING...');

        try {
            // ============ iOS FIX: Ensure AudioContext is ready ============
            if (window.audioContext && window.audioContext.state === 'suspended') {
                console.log('[Mobile] Resuming AudioContext...');
                await window.audioContext.resume();
            }

            // ============ iOS FIX: Request mic synchronously ============
            console.log('[Mobile] Requesting microphone...');
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Stop tracks so SDK can use the mic
            stream.getTracks().forEach(track => track.stop());

            // Small delay to ensure mic is released
            await new Promise(resolve => setTimeout(resolve, 150));

            // ============ iOS FIX: Audio routing for headphones ============
            if (navigator.audioSession && navigator.audioSession.type !== 'play-and-record') {
                try {
                    navigator.audioSession.type = 'play-and-record';
                    console.log('[Mobile] Set audioSession to play-and-record');
                } catch (e) {
                    // Not supported on all browsers
                }
            }

            // Now start the conversation
            const randomMessage = getRandomFirstMessage();
            console.log('Starting with message:', randomMessage);

            conversation = await Conversation.startSession({
                agentId: agentId,
                overrides: {
                    agent: {
                        firstMessage: randomMessage
                    }
                },
                onConnect: () => {
                    console.log('Connected to ElevenLabs');
                    isConnecting = false;
                    callButton.classList.remove('connecting');
                    callButton.classList.add('active');
                    callIcon.textContent = '📵';
                    updateStatus('connected', 'CONNECTED');
                    setMood('happy');
                    blink();
                    setTimeout(() => setMood('neutral'), 1000);
                },
                onDisconnect: () => {
                    console.log('Disconnected');
                    conversation = null;
                    isConnecting = false;
                    callButton.classList.remove('active', 'connecting');
                    callIcon.textContent = '📞';
                    updateStatus('disconnected', 'OFFLINE');
                    isSpeaking = false;
                    targetAmplitude = 0;
                    setMood('neutral');
                },
                onError: (error) => {
                    console.error('Conversation error:', error);
                    isConnecting = false;
                    showError(error.message || 'Connection error');
                    setMood('sad');
                    setTimeout(() => setMood('neutral'), 2000);
                },
                // ... rest of callbacks ...
            });
        } catch (error) {
            console.error('Failed to start conversation:', error);
            isConnecting = false;
            callButton.classList.remove('connecting');
            callIcon.textContent = '📞';
            updateStatus('disconnected', 'OFFLINE');

            if (error.name === 'NotAllowedError') {
                showError('Microphone access denied. Please allow microphone in browser settings.');
            } else if (error.name === 'NotFoundError') {
                showError('No microphone found. Please connect a microphone.');
            } else {
                showError(error.message || 'Failed to connect');
            }
            setMood('sad');
            setTimeout(() => setMood('neutral'), 2000);
        }
    }
};
```

---

## 4. Add Mobile-Specific UI Improvements (MEDIUM)

### Show "Tap to Enable Audio" on First Visit

```javascript
// Check if iOS and show hint
const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
if (isIOS && !sessionStorage.getItem('audioHintShown')) {
    showTranscription('Tap anywhere to enable audio', false);
    setTimeout(hideTranscription, 3000);
    sessionStorage.setItem('audioHintShown', 'true');
}
```

### Better Error Messages for Mobile

```javascript
function getMobileErrorMessage(error) {
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
        if (error.name === 'NotAllowedError') {
            return 'Microphone blocked. Go to Settings > Safari > Microphone and allow this site.';
        }
    }
    return error.message || 'Connection failed';
}
```

---

## 5. Add Debug Mode for Mobile Testing

Add this to help debug mobile issues:

```javascript
// Mobile debug helper
window.mobileDebug = function() {
    const info = {
        userAgent: navigator.userAgent,
        isIOS: /iPad|iPhone|iPod/.test(navigator.userAgent),
        isSafari: /^((?!chrome|android).)*safari/i.test(navigator.userAgent),
        audioContextState: window.audioContext?.state,
        audioContextSupport: !!window.AudioContext,
        mediaDevicesSupport: !!navigator.mediaDevices,
        getUserMediaSupport: !!navigator.mediaDevices?.getUserMedia,
        webRTCSupport: !!window.RTCPeerConnection,
        audioSessionSupport: !!navigator.audioSession
    };
    console.table(info);
    return info;
};

// Auto-log on page load for debugging
if (location.search.includes('debug')) {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('=== Mobile Debug Info ===');
        window.mobileDebug();
    });
}
```

---

## 6. Connection Type Consideration

ElevenLabs SDK supports both WebSocket and WebRTC connections. WebRTC has better audio quality but may have more issues on iOS:

```javascript
conversation = await Conversation.startSession({
    agentId: agentId,
    connectionType: 'websocket',  // Try 'websocket' if 'webrtc' has issues
    // ...
});
```

---

## Testing Checklist

- [ ] Test on iPhone Safari (standalone, not in-app browser)
- [ ] Test on iPad Safari
- [ ] Test on Chrome iOS (uses Safari engine)
- [ ] Test on Android Chrome
- [ ] Test with Bluetooth headphones connected
- [ ] Test with wired headphones
- [ ] Test after denying microphone permission (should show helpful error)
- [ ] Test after granting microphone permission
- [ ] Test wake word functionality on mobile
- [ ] Test camera + voice simultaneously

---

## Sources

- [ElevenLabs React SDK](https://elevenlabs.io/docs/agents-platform/libraries/react)
- [ElevenLabs Troubleshooting](https://help.elevenlabs.io/hc/en-us/sections/13415989887889-Troubleshooting)
- [iOS AudioContext Fix](https://gist.github.com/kus/3f01d60569eeadefe3a1)
- [WebRTC Safari Guide](https://webrtchacks.com/guide-to-safari-webrtc/)
