# iOS Safari AudioContext Fix

## The Problem

iOS Safari requires the AudioContext to be "warmed up" from a user interaction before any audio playback will work. This affects:
- Voice agent audio output
- Any Web Audio API usage
- MediaStream audio playback

## Solution 1: Touch-to-Activate Pattern (Recommended)

Add this script early in your page to capture the first user touch and activate audio:

```javascript
// iOS Safari AudioContext Fix
// Must be added BEFORE any audio functionality

(function() {
    // Create AudioContext early
    window.AudioContext = window.AudioContext || window.webkitAudioContext;

    if (window.AudioContext) {
        window.audioContext = new window.AudioContext();
    }

    var fixAudioContext = function(e) {
        if (window.audioContext) {
            // Create and play a silent buffer to "unlock" audio
            var buffer = window.audioContext.createBuffer(1, 1, 22050);
            var source = window.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(window.audioContext.destination);

            // Use appropriate method for browser version
            if (source.start) {
                source.start(0);
            } else if (source.play) {
                source.play(0);
            } else if (source.noteOn) {
                source.noteOn(0);
            }

            // Also resume the context
            if (window.audioContext.state === 'suspended') {
                window.audioContext.resume();
            }
        }

        // Only need to do this once
        document.removeEventListener('touchstart', fixAudioContext);
        document.removeEventListener('touchend', fixAudioContext);
        document.removeEventListener('click', fixAudioContext);
    };

    // Listen for first interaction
    document.addEventListener('touchstart', fixAudioContext);
    document.addEventListener('touchend', fixAudioContext);
    document.addEventListener('click', fixAudioContext);
})();
```

Source: [GitHub Gist by Blake Kus](https://gist.github.com/kus/3f01d60569eeadefe3a1)

## Solution 2: Simple Resume on Touch (Modern)

For modern browsers, a simpler approach may work:

```javascript
// Simple iOS audio fix
document.addEventListener('touchend', () => {
    if (window.audioContext && window.audioContext.state === 'suspended') {
        window.audioContext.resume();
    }
}, { once: true });
```

## Solution 3: Pre-Click Activation Modal

Show a modal/splash screen that requires user to tap before starting the voice agent:

```html
<div id="start-modal" class="modal">
    <div class="modal-content">
        <h2>Tap to Start</h2>
        <p>For voice features to work, tap the button below.</p>
        <button id="start-button">Start Voice Agent</button>
    </div>
</div>

<script>
document.getElementById('start-button').addEventListener('click', async () => {
    // This click IS the user gesture

    // 1. Warm up AudioContext
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    await audioContext.resume();

    // 2. Request microphone (while still in gesture handler)
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Keep stream for later or stop tracks
        stream.getTracks().forEach(track => track.stop());
    } catch (e) {
        console.log('Mic permission denied');
    }

    // 3. Hide modal and enable voice features
    document.getElementById('start-modal').style.display = 'none';

    // Voice agent is now ready to use
});
</script>
```

## Implementation for Pi-Guy

### Current Issue

The current implementation calls `Conversation.startSession` inside the button click handler, which should work. However, there may be issues with:

1. Async operations before audio starts
2. The SDK creating its own AudioContext without warming it up
3. Race conditions with microphone access

### Recommended Changes

Add this to `index.html` in the `<head>` section, BEFORE the ElevenLabs SDK:

```html
<script>
// iOS Safari Audio Fix - must run before any audio SDK
(function() {
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    if (window.AudioContext) {
        window.audioContext = new window.AudioContext();
    }

    var audioUnlocked = false;

    var unlockAudio = function(e) {
        if (audioUnlocked) return;

        if (window.audioContext) {
            // Play silent buffer
            var buffer = window.audioContext.createBuffer(1, 1, 22050);
            var source = window.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(window.audioContext.destination);
            if (source.start) source.start(0);

            // Resume if suspended
            if (window.audioContext.state === 'suspended') {
                window.audioContext.resume().then(() => {
                    console.log('AudioContext resumed');
                    audioUnlocked = true;
                });
            } else {
                audioUnlocked = true;
            }
        }
    };

    // Capture ALL potential user gestures
    ['touchstart', 'touchend', 'click', 'keydown'].forEach(function(event) {
        document.addEventListener(event, unlockAudio, { passive: true });
    });

    // Expose for debugging
    window.isAudioUnlocked = function() { return audioUnlocked; };
})();
</script>
```

### Modify toggleConversation

Ensure microphone is requested SYNCHRONOUSLY in the click handler:

```javascript
window.toggleConversation = async function() {
    // ... existing checks ...

    if (!conversation) {
        // Ensure AudioContext is unlocked
        if (window.audioContext && window.audioContext.state === 'suspended') {
            await window.audioContext.resume();
        }

        // Request microphone FIRST, synchronously in click handler
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Release for SDK to use
        } catch (e) {
            showError('Microphone access denied');
            return;
        }

        // Small delay to ensure mic is released
        await new Promise(resolve => setTimeout(resolve, 100));

        // NOW start the conversation
        conversation = await Conversation.startSession({
            agentId: agentId,
            // ... rest of config ...
        });
    }
};
```

## Testing on iOS

1. Open Safari on iPhone/iPad
2. Go to the page
3. Check console for "AudioContext resumed" message
4. Tap the call button
5. If issues persist, check console for errors

## Debugging

Add this to check audio state:

```javascript
// Debug audio state
window.debugAudio = function() {
    console.log('AudioContext state:', window.audioContext?.state);
    console.log('Audio unlocked:', window.isAudioUnlocked?.());
    console.log('User agent:', navigator.userAgent);
    console.log('Is iOS:', /iPad|iPhone|iPod/.test(navigator.userAgent));
};
```

## Sources

- [iOS AudioContext Fix Gist](https://gist.github.com/kus/3f01d60569eeadefe3a1)
- [Stack Overflow - Cannot resume AudioContext in Safari](https://stackoverflow.com/questions/57510426/cannot-resume-audiocontext-in-safari)
- [WebKit Blog - Web Audio](https://webkit.org/blog/7763/a-closer-look-into-webrtc/)
