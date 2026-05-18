# Editing Instructions for Qwen Image Edit

Qwen Image Edit takes a source image (or multiple images) plus a natural-language instruction and outputs an edited image. The same Qwen Image 2.0 model handles both generation and editing — unlike Flux, which needs separate workflows.

This reference covers how to write effective edit instructions for each editing capability.

The core principle across all edits: **name what changes, and name what stays.** Without explicit preservation language, Qwen Edit can drift on elements you didn't intend to modify.

---

## Capability 1: Semantic editing

Change *what's in* the image — clothing, hair, expression, pose, time of day, weather, season, etc.

**Template:**
> Change [specific element] [to/from specific target]. Keep [list of preserved elements] exactly as in the source image.

**Examples:**

*Hair color change:*
> Change the woman's hair color from black to warm auburn red. Keep her facial features, expression, skin tone, clothing, pose, and the background exactly as in the source. Match the new hair color naturally to the existing lighting on her face.

*Outfit change:*
> Change the man's t-shirt to a navy blazer over a white button-down shirt. Keep his face, hair, expression, body pose, and the background entirely unchanged. The new clothing should fit his pose naturally and match the lighting of the original photo.

*Time of day:*
> Change the scene from daytime to dusk. Soften the sunlight into warm golden hour tones with longer shadows, and add a hint of orange and pink in the sky. Keep all subjects, objects, and the composition identical to the source.

*Weather:*
> Add light rain to the scene. Wet the pavement so it reflects the lights, add subtle vertical rain streaks across the frame, and slightly desaturate the colors. Keep all people, vehicles, buildings, and the framing exactly as in the source.

*Expression:*
> Change the subject's expression from neutral to a warm, genuine smile that reaches her eyes. Keep her face structure, hair, clothing, pose, and the background unchanged. The smile should look natural for her face, not exaggerated.

---

## Capability 2: Appearance / quality editing

Fix problems with an existing image — remove unwanted elements, restore quality, adjust lighting.

**Examples:**

*Object removal:*
> Remove the trash can from the lower-left corner of the image. Replace that area with the brick pavement texture that continues from the surrounding area. Keep all other elements — the person, the storefront behind them, the lighting — exactly as in the source.

*Watermark removal:*
> Remove the watermark from the lower-right corner of the image. Reconstruct the underlying scene cleanly. Keep all other parts of the image unchanged.

*Lighting correction:*
> Brighten the subject's face, which is currently in deep shadow, while keeping the rest of the photo's exposure unchanged. The added light should look like soft natural fill light from the front, not artificial. Preserve all facial features, the original background light direction, and the overall color grading.

*Color correction:*
> Adjust the color balance: the current image has a strong green tint. Neutralize the greens and restore natural skin tones. Keep all subjects, objects, composition, and the overall lighting setup unchanged.

---

## Capability 3: Text editing

Add, remove, or change text in an image.

**Important:** when editing text, quote both the original text (what's being replaced) and the new text (what replaces it). This helps Qwen find the right element to modify.

**Examples:**

*Replace text on a sign:*
> Replace the sign currently reading "OPEN" with a sign reading "CLOSED FOR HOLIDAYS". Match the original sign's font style, color, size, and position exactly. Keep the sign's frame, the storefront, the lighting, and everything else in the image identical to the source.

*Add new text:*
> Add a poem in calligraphy in the upper-left corner of the image, written vertically from top to bottom, right to left. The text should read "The river flows east, washing away heroes of ages past." Use traditional Chinese calligraphy style in deep ink with appropriate brush variation, sized to fit naturally in the upper-left quadrant without overlapping the main subject. Keep all other elements of the image unchanged.

*Remove text:*
> Remove the "SALE 50% OFF" text overlay from the upper portion of the image. Reconstruct the storefront window and the products visible behind it as they would appear without the overlay. Keep everything else in the image identical to the source.

*Change language:*
> Replace the English text on the menu, which currently reads "Daily Specials", with Chinese text reading "今日特餐" (jīnrì tècān). Match the original's font weight, color, and position. Keep the rest of the menu layout, the surrounding restaurant, and the lighting unchanged.

---

## Capability 4: View synthesis (rotation)

Show a different angle of the subject — particularly useful for product photography and character design.

**Examples:**

*90° rotation:*
> Rotate the subject 90 degrees clockwise, showing the right side of the object. Keep the lighting setup, the background, the surface the object sits on, and the overall photographic style consistent with the source image. The new view should be plausible as a continuation of the original shoot.

*180° rotation:*
> Rotate the subject 180 degrees, showing the back of the object. Render the back accurately based on visible cues from the source — any straps, seams, labels, or design elements that suggest what the back should look like. Keep the lighting, background, surface, and photographic style identical to the source.

*Character turnaround:*
> Show the same character from a three-quarter rear view. The character's hairstyle, clothing, body proportions, and any visible accessories should remain identical. The background and lighting should match the source.

---

## Capability 5: Multi-image fusion

Combine elements from multiple source images into one output.

**Important:** when working with multiple images, refer to them by number — "Image 1", "Image 2", etc. Be explicit about which element comes from which source.

**Examples:**

*Group photo composite:*
> Merge the person from Image 1 and the person from Image 2 into a natural group photo. Both standing side by side, 30 cm apart, using the background from Image 2. 50mm lens, f/4.0, warm natural lighting matched to Image 2's environment, no visible compositing seams. Both subjects should appear lit by the same light source as Image 2's background suggests.

*Subject + new background:*
> Place the subject from Image 1 into the background from Image 2. Match the subject's lighting to Image 2's environment — Image 2 has overcast cool daylight, so adjust the subject's lighting from the original warm key to match. Keep the subject's pose, clothing, and facial features identical. The subject should occupy the right third of the new composition.

*Style transfer from reference:*
> Apply the painting style of Image 1 (an oil painting with thick impasto brushwork) to the subject and scene from Image 2 (a photograph of a city street). Keep the composition, perspective, and subjects of Image 2, but render every surface with the visible brushwork and color palette of Image 1.

*Cross-domain placement:*
> Use the city photo as Image 1 (the base). Keep all real buildings, streets, and vehicles unchanged. Add three cartoon characters from Image 2 (a children's book illustration) around the buildings — one sitting on top of the tallest building, one peeking from the right side of the foreground, one sitting on the ground in front. The cartoon characters should retain their illustrated style despite the photographic background.

---

## Capability 6: Layout edits

Change the composition or framing of an image.

**Examples:**

*Add headroom:*
> Extend the image upward by approximately 30%, generating sky and atmosphere consistent with the existing scene. Keep all current image content unchanged in its current position; only generate new content above the current top edge.

*Outpainting:*
> Outpaint the image to the right by 50%, continuing the scene naturally. The new area should show more of the same street, with consistent architecture, lighting, and atmosphere. Don't add new prominent elements — just extend what's there.

*Crop and recompose:*
> Recompose the image as a 9:16 vertical crop centered on the main subject. The subject should occupy the central third of the new frame. If needed, generate small amounts of new image at the top and bottom to maintain the subject's proportions and breathing room.

---

## Writing principles for edits

### Be surgical, not sprawling
Edit instructions should be short and specific. Don't pile on style descriptions or atmospheric flourishes — those are for generation, not editing. The fewer words you change, the more reliably Qwen preserves what you don't mention.

### Always include preservation language
Even when it feels obvious, name what should stay:
- "Keep the background unchanged."
- "Preserve the subject's facial features."
- "All other elements remain identical to the source."

Without this, drift happens. The subject's earrings change. The wallpaper pattern subtly shifts. The lighting direction slips by ten degrees.

### Use spatial language for placement
Qwen Edit handles "upper-left corner", "directly below", "to the right of the existing X" very well. Lean on these.

### For complex edits, sequence them
If a user wants three changes (hair color + outfit + background), it's often more reliable to do three sequential edits than one combined edit. Note this to the user.

### Match the source's photographic style
When editing photos, match the original's lighting direction, depth of field, and color grading. Without this, the edited element will look pasted-on.

### For text edits, lower the guidance_scale slightly
Edits work better with `guidance_scale: 3.0–4.0` than the 4.0–5.0 used for text generation. The model needs more flexibility to preserve unedited parts while changing the targeted text.

---

## Common pitfalls

**Drift on unintended elements:**
- Add more explicit preservation language
- Be very specific about what's being changed
- For multi-step edits, run them sequentially

**Edit doesn't take effect:**
- Be more explicit about the target — "the woman's hair, which is currently black" works better than "her hair"
- Raise guidance_scale to 4.0
- For subtle changes (lighting tweaks, color shifts), describe the desired outcome more concretely

**Composited element looks pasted-on:**
- Specify lighting matching: "lit by the same source as the background"
- Specify color matching: "color graded to match the cool tones of the original photo"
- Specify depth/scale: "at the same depth of field as the original subject"

**Text edit produces wrong layout:**
- Specify font style, color, AND position to match the original
- For replacement, quote both old and new text
- For added text, describe alignment and orientation explicitly

---

## Parameter recommendations for edits

- **General edits:** `guidance_scale: 3.5`, `num_inference_steps: 30`
- **Subtle edits (lighting tweaks, color adjustments):** `guidance_scale: 3.0`, `num_inference_steps: 25`
- **Heavy edits (composition changes, multi-image fusion):** `guidance_scale: 4.0`, `num_inference_steps: 35–40`
- **Text edits:** `guidance_scale: 4.0`, `num_inference_steps: 35`
