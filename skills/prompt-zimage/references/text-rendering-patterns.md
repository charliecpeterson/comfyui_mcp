# Text-Rendering Patterns

Z-Image's bilingual text rendering (English + Chinese) is exceptional — better than Flux 1 and competitive with Qwen Image 2.0 and Flux 2 Flex. This file catalogues patterns for the common text-heavy use cases.

The single most important rule: **wrap exact text in double quotation marks**, and **each separate text element gets its own quoted block with its own style description**.

Z-Image's strong prompt adherence means it will faithfully follow your text instructions — but it'll also faithfully include whatever ambiguous extras you leave in. Be specific about what text appears AND what doesn't.

---

## Core conventions (all patterns)

1. **Quote every literal piece of text.** Anything you want rendered as text on the image goes inside `" "`.
2. **Front-load the most important text.** Z-Image weighs early tokens more — primary headlines should appear in the first third of the prompt.
3. **Describe font style alongside each text element.** "bold sans-serif", "elegant serif", "weathered hand-painted", "calligraphic brushwork", "art deco geometric letterforms", "neon script", "vintage typewriter".
4. **Describe placement explicitly.** "centered at the top", "in the lower-right corner", "directly below the title", "running along the bottom edge".
5. **Add a "no additional text" clause for text-only-or-no-text rendering.** Z-Image will sometimes invent additional signage if you don't specify. Adding "no additional text, no extra signage, no other writing visible" near the end of the prompt prevents this.
6. **For Z-Image-Turbo:** `guidance_scale: 0.0` (mandatory — CFG is disabled in the distilled model). Steps 8–9.
7. **For Z-Image base:** `guidance_scale: 4.5–5.5` for text fidelity. Steps 30–40.

---

## Pattern 1: Single Sign or Storefront

The simplest text pattern. One main piece of text, optionally with a secondary element.

**Template:**
> [Scene with environment and lighting]. [Sign type and placement] reads "[EXACT TEXT]" in [font style]. [Optional secondary text]: "[SECONDARY TEXT]" in [smaller font style]. [Constraint cleanup: no other text].

**Example:**
> Vintage barbershop storefront at golden hour, brick facade with a single hanging sign. The hanging sign reads "FRANK'S BARBERS" in bold red distressed sans-serif on cream background. Below the door, a smaller painted notice reads "Walk-ins Welcome" in cursive script. Cinematic film still, 35mm lens, warm side-lighting from a low sun, no other text or signage visible on the storefront.

---

## Pattern 2: Multi-Element Poster

Posters typically have 4–6 distinct text elements with clear hierarchy. Describe each in order from largest/most prominent to smallest.

**Template:**
> [Poster style and color palette]. Title at the top reads "[MAIN TITLE]" in [font]. Below it, subtitle reads "[SUBTITLE]" in [font]. [Body content block]. At the bottom, [footer text] reads "[FOOTER]" in [font]. [Constraint cleanup].

**Example:**
> Bold rock concert poster, dark navy background with electric purple and orange spotlight beams. Main title at the top reads "ROCK FESTIVAL 2026" in massive distressed sans-serif. Below it, three featured bands listed in column: "Thunder Strike", "Neon Dreams", "Electric Soul". Date in smaller subheader reads "July 15–17". At the bottom, venue reads "Central Park Arena". Ticket information in a small corner banner reads "Early Bird $89". Edgy modern typography, high contrast, no additional text, no logos beyond the title, no watermarks.

**Variations:**
- **Movie poster:** Title near top → tagline below title → credit block at bottom in standardized billing-block style
- **Festival poster:** Title at top → lineup as visual hierarchy → date and location → ticket/sponsor info at bottom
- **Event poster:** Title → date/time → location → "RSVP" or other CTA

---

## Pattern 3: Tech Conference / Modern Layout

Z-Image is particularly good at clean modern tech-style posters (one of its most-shared use cases in community examples).

**Example:**
> A clean modern tech-conference poster on a deep indigo gradient background with glowing cyan circuit-line patterns. A massive bold headline at the top reads "FUTURE STACK 2026" in a thick sans-serif font. A smaller subtitle directly below reads "The AI Creators Summit" in lighter weight. Bottom-left line reads "San Francisco, June 10–12". High contrast, generous negative space, print-ready layout, no additional text or logos.

---

## Pattern 4: Presentation Slide

Slides have a title, subtitle/section indicator, body content, and often a footer or page number.

**Template:**
> [Slide background and color palette]. Title at the top-left reads "[TITLE]" in [font]. Below it, a thinner subtitle reads "[SUBTITLE]". Body content: [describe body elements with their own quoted text]. Footer at the bottom reads "[FOOTER]" in small text. [Constraint cleanup].

**Example:**
> Clean minimalist presentation slide, white background with a single accent color of deep teal. Title at the top-left reads "Q1 2026 Results" in bold sans-serif. Below it, a thinner subtitle reads "Internal review — Finance team" in matching teal. Main body shows three large stat blocks arranged left to right: left block reads "Revenue $2.4M" in heavy figures, middle block reads "Growth +18%" in green, right block reads "Customers 12,487" in navy. Footer at the bottom-right reads "Slide 4 of 12" in small grey text. No additional text or design elements, clean print-ready layout.

---

## Pattern 5: Infographic

Infographics combine layout, multiple text elements, and often data visualization.

**Template:**
> [Infographic style and color palette]. Title reads "[TITLE]". Three [or N] sections arranged [layout]. Section 1: "[header]" with [content and figures]. [Continue]. Source citation at the bottom reads "[SOURCE]".

**Example:**
> Clean modern infographic, white background with one accent color of forest green. Title at the top reads "Annual Coffee Consumption" in bold sans-serif. Three vertical bar groups arranged left to right, each labeled and topped with a figure. Left bar group labeled "Finland" with figure "12 kg/person". Middle bar group labeled "Norway" with figure "10 kg/person". Right bar group labeled "Sweden" with figure "8 kg/person". Source citation at the bottom-left reads "Source: International Coffee Organization, 2025" in small grey text. Editorial illustration style, clean composition, no extra annotations.

---

## Pattern 6: Storefront with Neon (Z-Image strength)

Z-Image renders neon-lit signage with reflections particularly well — one of its showcase use cases.

**Example:**
> A rain-soaked Tokyo alleyway at night, narrow and atmospheric. A vertical neon shop sign at eye level glows in hot pink: the top characters read "未来餐厅" in Chinese kanji, with English text "FUTURE KITCHEN" glowing in the same hot pink below them. Puddles on the wet asphalt reflect the neon glow, smearing pink and cyan light across the foreground. Shot on a Leica Q3 with anamorphic lens flare, teal-and-magenta cinematic color grade, 16:9 aspect ratio, no additional signage visible, no extra text.

---

## Pattern 7: Menu / Price List

Menus have a header, a list of items with prices, and often section breaks.

**Template:**
> [Menu style and color palette]. Header reads "[RESTAURANT NAME]". Section header: "[SECTION]". Items listed: "[Item 1]" — "[price]", "[Item 2]" — "[price]", "[Item 3]" — "[price]". [Continue with sections]. Footer: "[footer text]".

**Example:**
> Elegant cafe menu printed on cream-colored paper with a soft sage-green border. Header at the top reads "MILLIE'S COFFEE" in elegant English serif. Below it, smaller text reads "Established 1952" in italic. First section header reads "ESPRESSO". Items listed under it: "Single Espresso" priced "$3.50", "Double Espresso" priced "$5", "Cortado" priced "$4.50". Second section header reads "POUR-OVER". Items listed: "Ethiopia Yirgacheffe" priced "$6", "Colombia Huila" priced "$5.50". Footer at the bottom reads "All beans roasted weekly on site". Hand-illustrated coffee-cup motif in the upper-right corner, no additional menu items or text.

---

## Pattern 8: Book Cover

Book covers have a title, author, and often a tagline or genre indicator.

**Example:**
> Minimalist literary fiction book cover, off-white background with a single small color image centered. Title in the upper third reads "The Lighthouse Keeper" in tall thin serif, italic. Centered cover art is a small ink illustration of a single lighthouse against a stormy sky. Author name at the bottom reads "Eleanor Marsh" in smaller matching serif. Above the author name, a slim tagline reads "A novel". Generous white space throughout, clean editorial composition, no additional design elements.

---

## Pattern 9: Storyboard / Multi-Panel Layout

Z-Image handles multi-panel storyboards well — useful for skincare launches, product narratives, ad concepts.

**Example:**
> Horizontal three-panel storyboard for a minimalist skincare serum launch, clean white gallery background across all panels. Panel 1: a 32-year-old adult woman with loose chestnut hair and a soft linen robe examining tired skin in a round brass vanity mirror, cool morning window light, subtle under-eye shadows, honest not glamorized. Panel 2: close-up of her hands dispensing a single golden drop of serum from a frosted glass bottle labeled "LUMA", amber liquid catching the light, manicured but natural nails. Panel 3: the same woman an hour later in warm afternoon light, visibly refreshed, gentle smile, dewy cheek highlight, the bottle placed beside her on a marble counter with a small white price tag reading "$48". Uniform color grading shifting cool to warm across panels, shot on Hasselblad X2D with 90mm lens, commercial editorial style, hyper-detailed skin textures, clean sans-serif captions "TIRED", "APPLY", "GLOW" beneath each panel respectively, 16:9 aspect ratio, no additional text.

---

## Pattern 10: Social Media Graphic

Social graphics emphasize bold typography over busy imagery.

**Example:**
> Bold 1:1 social media quote graphic, deep navy background with a single yellow accent. Primary text fills the center of the frame and reads "Done is better than perfect" in large bold sans-serif. Below the quote, in much smaller text, an attribution reads "— Sheryl Sandberg". A tiny yellow underline runs beneath the attribution. Clean minimal composition, no additional design elements, no logos.

---

## Pattern 11: Album Cover / Music Imagery

Z-Image handles album covers and retro-style music imagery well — another showcased strength.

**Example:**
> A retro 1980s synthwave album cover. A grid landscape leading to a setting purple sun in the distance. A chrome sports car driving away into the distance along the central grid road. The text "NIGHT DRIVE" is written in a metallic chrome script font with neon pink outlines, floating in the sky above the sun. Below the title in much smaller matching script, the artist name reads "Lumen Wave". Deep purple and magenta color palette, scan-line texture, no additional text.

---

## Common pitfalls and fixes

**Garbled text:**
- For Turbo: raise resolution to 1280×720 or use a longer, more specific prompt
- For base: raise guidance_scale to 5.0–5.5
- Shorten the text — Z-Image handles 1–8 word phrases more reliably than full sentences
- Front-load it earlier in the prompt
- Add "clean typography, sharp lettering" to the prompt

**Unwanted extra text appearing:**
- Add explicit cleanup clauses: "no additional text, no extra signage, no other writing visible, no logos"
- Be more specific about what surface the text is on (sign, banner, screen) — Z-Image is less likely to invent text on unspecified surfaces
- For base/Omni: add `text artifacts, extra writing, garbled text` to the negative prompt

**Wrong font style:**
- Be more specific — "weathered hand-painted serif with chipped paint" beats "old-looking font"
- Reference real typographic eras — "art deco letterforms", "Bauhaus geometric sans", "1980s synthwave chrome script"

**Text in wrong position:**
- Use explicit spatial language and be redundant if needed: "centered at the very top of the image, occupying the upper 20% of the frame, with generous space below"
- For tight constraints, describe the position twice in different ways

**Multi-line text breaks weirdly:**
- Either describe how it should break ("title on two lines, first line 'QUIET' second line 'STREETS'") or use shorter text

**Numbers/dates rendered incorrectly:**
- For prices, include the currency symbol explicitly: "$89" beats "89 dollars"
- For dates, use full formats: "June 10–12" beats "6/10–12"

---

## When to use Z-Image versus alternatives for text

Z-Image is at its best for:

- Bilingual English + Chinese signage
- Storefronts and atmospheric scenes with integrated text
- Retro / synthwave / 80s aesthetic posters
- Tech-conference modern posters
- Quick iteration on text concepts (Turbo's speed)

Compare to alternatives:

- **vs Qwen Image 2.0:** Z-Image is faster and runs on smaller hardware; Qwen 2.0 handles longer, more complex multi-element layouts better. For a single sign or a poster with 3–5 text elements, Z-Image. For an infographic with 10+ elements, Qwen.
- **vs Flux 2 Flex:** Z-Image wins on Chinese; Flex wins on very specific Latin typographic styles. Z-Image is open-weights and free; Flex is API-only.
- **vs Pony/Illustrious:** different worlds — Pony/Illustrious can't render text reliably at all.
