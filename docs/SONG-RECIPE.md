# Song Generation Recipe

A guide for generating quality tracks using Suno API with style tags and thematic direction.

**Key Insight:** Don't write full lyrics - Suno does that well on its own. Focus on:
1. **Style/Audio Tags** - The sound, beat, production elements
2. **Theme/Direction** - A brief idea or story concept (1-2 sentences)

---

## Style Tag Categories

### Genre Tags (pick 1-2)
```
hip-hop, rap, r&b, trap, boom bap, lo-fi hip-hop
country hip-hop, southern rap, west coast, east coast
comedy rap, parody, satirical
soul, neo-soul, funk
pop, indie pop, electropop
rock, alternative, indie rock
```

### Beat/Rhythm Tags (pick 2-3)
```
heavy bass, sub-bass, 808s, hard-hitting drums
repetitive hi-hat, crisp snares, punchy kicks
syncopated drums, offbeat, swing rhythm
boom bap drums, classic hip-hop beat
trap beat, drill beat, bouncy beat
slow groove, laid-back tempo, mid-tempo
uptempo, high energy, fast flow
```

### Production/Texture Tags (pick 2-4)
```
hypnotic layers, atmospheric, spacey
piano-driven, keys, melodic piano
guitar loops, acoustic guitar, electric guitar
orchestral, strings, cinematic
minimal production, stripped-back, raw
layered vocals, vocal harmonies, ad-libs
reverb-heavy, echo effects, delay
distorted, gritty, lo-fi
clean mix, polished, radio-ready
vinyl crackle, dusty samples, old school
```

### Mood/Energy Tags (pick 1-2)
```
energetic, hype, aggressive, intense
mellow, chill, relaxed, smooth
emotional, introspective, reflective
dark, moody, atmospheric
uplifting, triumphant, anthemic
playful, fun, lighthearted
gritty, street, raw
confident, swagger, braggadocious
```

### Vocal Style Tags (pick 1-2)
```
male vocals, deep voice, raspy vocals
smooth delivery, melodic rap, sung-rap
fast flow, rapid-fire, double-time
laid-back flow, conversational, storytelling
aggressive delivery, intense, shouty
auto-tune, vocoder, pitch-shifted
```

---

## Proven Tag Combinations

### Formula: [Genre] + [Beat] + [Production] + [Mood] + [Vocal]

**For tracks like "Bassline Inferno" / "Bassquake Bounce":**
```
hip-hop, heavy bass, 808s, punchy kicks, hypnotic layers, energetic, aggressive delivery
```

**For tracks like "Lunchbox Dreams" / "Mama's Crown":**
```
hip-hop, boom bap drums, piano-driven, mellow, introspective, storytelling flow
```

**For tracks like "Bulletproof Thoughts":**
```
hip-hop, crisp snares, atmospheric, layered vocals, confident, mid-tempo
```

**For tracks like "Rapid Fire Symphony":**
```
hip-hop, fast hi-hats, minimal production, intense, rapid-fire flow, raw
```

**For tracks like "Straight Outta Laughs":**
```
comedy rap, trap beat, bouncy, playful, ad-libs, uptempo
```

**For tracks like "Dust on the Keys":**
```
country hip-hop, acoustic guitar, piano, mellow, storytelling, emotional
```

---

## Theme/Direction Examples

Keep it brief (1-2 sentences). Give Suno a concept, not a script.

### Street/Hustle Themes
- "Song about grinding from nothing, proving doubters wrong"
- "Coming up from the streets, success mindset"
- "Urban survival, staying sharp, trust no one"
- "Making it out the hood, celebrating success"

### Emotional/Personal Themes
- "Tribute to a hardworking mother who sacrificed everything"
- "Reflecting on struggle but staying hopeful"
- "Finding peace through music despite chaos"
- "Blue collar pride, working man's anthem"

### Fun/Comedy Themes
- "Parody of gangsta rap flexing but with mundane items"
- "Absurd brags and ridiculous punchlines"
- "Taking rap tropes and making them silly"

### Industry/Trade Themes (for SprayFoamRadio)
- "Pride in the spray foam trade, blue collar anthem"
- "Day in the life of an insulation installer"
- "Building something real, craftsmanship pride"

---

## Full Prompt Template

```
Style: [tag], [tag], [tag], [tag], [tag]

Theme: [1-2 sentence direction/story concept]

Title: [optional - let Suno pick if unsure]
```

### Example Prompts

**Example 1 - Hard Street Track:**
```
Style: hip-hop, heavy bass, 808s, repetitive hi-hat, hypnotic layers, energetic, aggressive delivery

Theme: Coming up from nothing, proving everyone wrong, unstoppable mindset
```

**Example 2 - Emotional/Reflective:**
```
Style: hip-hop, boom bap, piano-driven, mellow, introspective, storytelling flow, atmospheric

Theme: Tribute to the struggles of growing up poor but dreaming big
```

**Example 3 - Comedy:**
```
Style: comedy rap, trap beat, bouncy, playful, ad-libs, fun

Theme: Parody flexing about mundane things like Pringles and discount clothes
```

**Example 4 - Country Fusion:**
```
Style: country hip-hop, acoustic guitar, piano, slow groove, storytelling, emotional, raspy vocals

Theme: Finding solace in music when life gets hard
```

**Example 5 - High Energy Banger:**
```
Style: trap, hard-hitting drums, 808s, fast hi-hats, synth layers, hype, double-time flow

Theme: Rapid-fire skills, dominating the game, can't be stopped
```

---

## Tags That Work Well Together

### Heavy/Hard Sound
```
heavy bass + 808s + punchy kicks + aggressive + energetic
```

### Smooth/Chill Sound
```
mellow + piano-driven + laid-back + smooth delivery + atmospheric
```

### Classic/Boom Bap Sound
```
boom bap drums + vinyl crackle + old school + storytelling + raw
```

### Modern Trap Sound
```
trap beat + 808s + fast hi-hats + auto-tune + hype
```

### Emotional/Deep Sound
```
piano + strings + introspective + emotional + storytelling flow
```

---

## Suno API Parameters

When generating via API:

```json
{
  "model": "V5",
  "customMode": true,
  "style": "[your style tags here]",
  "prompt": "[your theme/direction here]",
  "vocalGender": "m",
  "styleWeight": 0.65,
  "weirdnessConstraint": 0.4,
  "instrumental": false
}
```

**Parameter Notes:**
- `styleWeight`: 0.65 is good balance (higher = more strict to style)
- `weirdnessConstraint`: 0.4 keeps it accessible (higher = more experimental)
- `vocalGender`: "m" for male, "f" for female

---

## What NOT to Do

1. **Don't write full lyrics** - Suno handles this well
2. **Don't overload tags** - 5-7 tags max
3. **Don't mix conflicting tags** - e.g., "aggressive" + "chill"
4. **Don't be too specific** - "song about a guy named John who..." is too narrow
5. **Don't use negative tags excessively** - they can confuse generation

---

## Quick Reference: Best Performing Tags

Based on analysis of 16 successful tracks:

**Most Common in Good Tracks:**
- `hip-hop` (14/16)
- `heavy bass` or `808s` (10/16)
- `energetic` or `mellow` (12/16)
- `layered` or `atmospheric` (8/16)
- `storytelling` or `confident` (9/16)

**Winning Combos:**
1. `hip-hop, 808s, atmospheric, energetic, confident`
2. `hip-hop, piano, mellow, introspective, storytelling`
3. `comedy rap, trap, bouncy, playful, ad-libs`

---

## Song Length Tips

- Short prompt = shorter song (30-60s)
- More detailed theme = longer song (60-120s)
- Use "extended" or "full-length" in style tags for longer tracks
- Auto-extend feature kicks in for songs under 60s

---

*Last updated: 2024-12-14*
*Based on analysis of generated_music/ tracks*
