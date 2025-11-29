# Mobile Browser Microphone Issues

## Overview

This document covers known issues with microphone access on mobile browsers, particularly iOS Safari, and solutions for the Pi-Guy voice agent.

## The Core Problem

Mobile browsers (especially iOS Safari) have strict requirements around:
1. **User gesture requirements** - Audio/mic must be initiated by user interaction
2. **AudioContext state** - Must be "warmed up" before playback works
3. **getUserMedia limitations** - Permission prompts may not count as user gestures
4. **Audio routing issues** - iOS may route audio to wrong output device

## Why It Works From Social Media Links

When clicking a link from social media apps (like iMessage, Facebook, etc.), the link opens in an **in-app browser** (SFSafariViewController or similar). These have different security contexts that may have already been "activated" by the tap gesture, allowing audio to work.

When opening directly in Safari (standalone), the page loads without a prior user gesture, causing audio issues.

---

## iOS Safari Specific Issues

### 1. AudioContext Starts Suspended

Safari creates AudioContext in a `suspended` state. It will NOT transition to `running` automatically - you must explicitly call `resume()` from a user gesture.

```javascript
// Safari behavior - AudioContext starts suspended
const audioContext = new AudioContext();
console.log(audioContext.state); // "suspended" on iOS Safari
```

### 2. User Gesture Requirements

Apple requires a user gesture (touchstart, touchend, click, keydown) to:
- Resume AudioContext
- Start audio playback
- Access the microphone (though the permission prompt doesn't count as a gesture)

**Critical:** The gesture must be **synchronous**. Calling these methods from a Promise or setTimeout chain may not work.

### 3. getUserMedia Doesn't Count as User Gesture

> "For whatever reason, Safari does not consider the iOS acceptance of the camera/mic usage dialog as a user gesture and there's no way to make camera capture count as a user gesture."
>
> Source: [webrtcHacks](https://webrtchacks.com/guide-to-safari-webrtc/)

### 4. Audio Routing Issues

iOS Safari may switch audio output to speakers when `getUserMedia` is called, even if headphones are connected.

**Workaround (2024):**
```javascript
// After calling getUserMedia
navigator.audioSession.type = 'play-and-record';
```

---

## ElevenLabs SDK Notes

### Package Migration

**Important:** The package `@11labs/client` is deprecated. Use `@elevenlabs/client` instead:

```javascript
// OLD (deprecated)
import { Conversation } from 'https://cdn.jsdelivr.net/npm/@11labs/client@latest/+esm';

// NEW (recommended)
import { Conversation } from 'https://cdn.jsdelivr.net/npm/@elevenlabs/client@latest/+esm';
```

### iOS Safari Preferences

From ElevenLabs SDK documentation:
> "iOS Safari seems to prefer the built-in speaker over headphones even when a bluetooth device is in use."

If you want to force headphones when available, use `preferHeadphonesForIosDevices` option:

```javascript
const conversation = await Conversation.startSession({
    agentId: 'your-agent-id',
    preferHeadphonesForIosDevices: true  // Not guaranteed to work
});
```

### Microphone Permissions

> "Conversational AI requires microphone access. Consider explaining and allowing microphone access in your app's UI before the Conversation kicks off. The microphone may also be blocked for the current page by default, resulting in the allow prompt not showing up at all."

---

## Browser Compatibility Notes

| Browser | Platform | Status | Notes |
|---------|----------|--------|-------|
| Chrome | iOS | Works | Uses Safari engine under the hood |
| Safari | iOS | Issues | Requires workarounds |
| Safari | macOS | Issues | Similar to iOS |
| Chrome | Android | Works | Best support |
| Firefox | Android | Works | Good support |
| Samsung Internet | Android | Works | Good support |

**Note:** On iOS, ALL browsers use Safari's WebKit engine due to Apple's restrictions. Chrome on iOS = Safari engine.

---

## WebRTC Limitations on iOS

> "WebRTC is only supported in Safari. No WKWebView, not even SFSafariViewController."
>
> Source: [webrtcHacks](https://webrtchacks.com/guide-to-safari-webrtc/)

This means:
- In-app browsers may not support WebRTC
- PWAs (Progressive Web Apps) may have issues
- Only standalone Safari has full WebRTC support

---

## Sources

- [ElevenLabs Troubleshooting](https://help.elevenlabs.io/hc/en-us/sections/13415989887889-Troubleshooting)
- [ElevenLabs Safari/iOS Issues](https://help.elevenlabs.io/hc/en-us/articles/16104020847249-Website-problems-with-Safari-iOS-iPhone-macOS-Mac)
- [ElevenLabs React SDK](https://elevenlabs.io/docs/agents-platform/libraries/react)
- [webrtcHacks Safari Guide](https://webrtchacks.com/guide-to-safari-webrtc/)
- [iOS Safari AudioContext Fix Gist](https://gist.github.com/kus/3f01d60569eeadefe3a1)
- [Stack Overflow - AudioContext Issues](https://stackoverflow.com/questions/57510426/cannot-resume-audiocontext-in-safari)
- [Stack Overflow - getUserMedia iOS Safari](https://stackoverflow.com/questions/53150556/accessing-microphone-with-the-help-of-getusermedia-on-ios-safari)
