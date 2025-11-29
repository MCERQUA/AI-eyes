# Quick Fixes for Mobile Microphone Issues

## TL;DR - Apply These Fixes

### Fix 1: Add iOS Audio Warmup (CRITICAL)

Add this BEFORE all other scripts in `<head>`:

```html
<script>
(function(){window.AudioContext=window.AudioContext||window.webkitAudioContext;if(!window.AudioContext)return;window.audioContext=new window.AudioContext();var u=false;function f(){if(u)return;var b=window.audioContext.createBuffer(1,1,22050);var s=window.audioContext.createBufferSource();s.buffer=b;s.connect(window.audioContext.destination);s.start?s.start(0):s.noteOn(0);window.audioContext.resume().then(function(){u=true;console.log('[iOS]Audio OK')}).catch(function(){});}['touchstart','touchend','click'].forEach(function(e){document.addEventListener(e,f,{passive:true});});})();
</script>
```

### Fix 2: Update SDK Package

Change import from:
```javascript
import { Conversation } from 'https://cdn.jsdelivr.net/npm/@11labs/client@latest/+esm';
```

To:
```javascript
import { Conversation } from 'https://cdn.jsdelivr.net/npm/@elevenlabs/client@latest/+esm';
```

### Fix 3: Add Audio Routing Fix

Add this in toggleConversation before starting session:

```javascript
// iOS audio routing fix
if (navigator.audioSession) {
    try { navigator.audioSession.type = 'play-and-record'; } catch(e) {}
}
```

### Fix 4: Pre-request Microphone

Add this before `Conversation.startSession`:

```javascript
// Pre-request mic
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
stream.getTracks().forEach(t => t.stop());
await new Promise(r => setTimeout(r, 150));
```

---

## Full Working Example

Here's the complete modified `<head>` section:

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pi-Guy Voice Agent</title>

    <!-- iOS Audio Fix - MUST BE FIRST -->
    <script>
    (function(){
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!window.AudioContext) return;
        window.audioContext = new window.AudioContext();
        var unlocked = false;
        function unlock() {
            if (unlocked) return;
            var buffer = window.audioContext.createBuffer(1, 1, 22050);
            var source = window.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(window.audioContext.destination);
            source.start ? source.start(0) : source.noteOn(0);
            window.audioContext.resume().then(function() {
                unlocked = true;
                console.log('[iOS] Audio unlocked');
            }).catch(function(){});
        }
        ['touchstart', 'touchend', 'click'].forEach(function(e) {
            document.addEventListener(e, unlock, { passive: true });
        });
        window.isAudioUnlocked = function() { return unlocked; };
    })();
    </script>

    <style>
        /* ... your styles ... */
    </style>

    <!-- Clerk Authentication -->
    <script async crossorigin="anonymous" ...></script>
</head>
```

---

## Test It

1. Deploy changes
2. Open Safari on iPhone
3. Open browser console (connect Mac + Safari Web Inspector)
4. Tap anywhere on page - should see "[iOS] Audio unlocked"
5. Tap call button
6. Should connect and work

If still broken, add `?debug` to URL and run `mobileDebug()` in console.
