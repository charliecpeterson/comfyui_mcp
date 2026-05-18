# Text-Rendering Patterns

Qwen Image's signature strength is professional-grade text rendering. This file is a catalogue of patterns for the common text-heavy use cases: signage, posters, slides, infographics, menus, packaging, book covers, social media graphics, and bilingual layouts.

The single most important rule across all patterns: **wrap exact text in double quotation marks**, and **each separate text element gets its own quoted block with its own style description**.

---

## Core conventions (all patterns)

1. **Quote every literal piece of text.** Anything you want rendered as text on the image goes inside `" "`.
2. **Front-load the most important text.** Qwen's bidirectional attention weights early tokens more — primary headlines should appear in the first third of the prompt.
3. **Describe font style alongside each text element.** "bold sans-serif", "elegant serif", "weathered hand-painted", "calligraphic brushwork", "art deco geometric letterforms", "neon script", "vintage typewriter".
4. **Describe placement explicitly.** "centered at the top", "in the lower-right corner", "directly below the title", "running along the bottom edge".
5. **Lean on Qwen's spatial reasoning.** Words like "above", "below", "to the left of", "centered between" are treated as compositional constraints, not decoration.
6. **For text-heavy work, set `guidance_scale: 4.5–5.0`** (higher CFG = better text fidelity).

---

## Pattern 1: Single Sign or Storefront

The simplest text pattern. One main piece of text, optionally with a secondary element.

**Template:**
> [Scene description with environment and lighting]. [Sign type / placement] reads "[EXACT TEXT]" in [font style]. [Optional secondary text]: "[SECONDARY TEXT]" in [smaller font style].

**Example:**
> Vintage barbershop storefront at golden hour, brick facade with a single hanging sign. Hanging sign reads "FRANK'S BARBERS" in bold red distressed sans-serif on cream background. Below the door, a smaller painted notice reads "Walk-ins Welcome" in cursive script. Cinematic film still, 35mm lens, warm side-lighting from a low sun.

---

## Pattern 2: Multi-Element Poster

Posters typically have 4–6 distinct text elements with clear hierarchy. Describe each in order from largest/most prominent to smallest.

**Template:**
> [Poster style and color palette]. Title at the top reads "[MAIN TITLE]" in [font]. Below it, subtitle reads "[SUBTITLE]" in [font]. [Body content block]. At the bottom, [footer text] reads "[FOOTER]" in [font].

**Example:**
> Bold rock concert poster, dark navy background with electric purple and orange spotlight beams. Main title at the top reads "ROCK FESTIVAL 2026" in massive distressed sans-serif. Below it, three featured bands listed in column: "Thunder Strike", "Neon Dreams", "Electric Soul". Date in smaller subheader reads "July 15–17". At the bottom, venue reads "Central Park Arena". Ticket information in a small corner banner reads "Early Bird $89". Edgy modern typography, high contrast.

**Variations:**
- **Movie poster:** Title near top → tagline below title → credit block at bottom in standardized "billing block" style
- **Festival poster:** Title at top → lineup as visual hierarchy → date and location → ticket/sponsor info at bottom
- **Event poster:** Title → date/time → location → "RSVP" or other CTA

---

## Pattern 3: Presentation Slide

Slides have a title, subtitle/section indicator, body content, and often a footer or page number. Describe each element with explicit positioning.

**Template:**
> [Slide background and color palette]. Title at the top-left reads "[TITLE]" in [font]. Below it, a thinner subtitle reads "[SUBTITLE]". Body content: [describe body elements with their own quoted text]. Footer at the bottom reads "[FOOTER]" in small text.

**Example:**
> Clean minimalist presentation slide, white background with a single accent color of deep teal. Title at the top-left reads "Q1 2026 Results" in bold sans-serif. Below it, a thinner subtitle reads "Internal review — Finance team". Main body shows three large stat blocks arranged left to right: left block reads "Revenue $2.4M" in heavy figures, middle block reads "Growth +18%" in green, right block reads "Customers 12,487". Footer at the bottom-right reads "Slide 4 of 12" in small grey text.

---

## Pattern 4: Infographic

Infographics combine layout, multiple text elements, and often data visualization. Describe the structure explicitly.

**Template:**
> [Infographic style and color palette]. Title reads "[TITLE]". Three [or N] sections arranged [layout]. Section 1: "[header]" with [content and figures]. Section 2: ... [continue]. Source citation at the bottom reads "[SOURCE]".

**Example:**
> Clean modern infographic, white background with one accent color of forest green. Title at the top reads "Annual Coffee Consumption" in bold sans-serif. Three vertical bar groups arranged left to right, each labeled and topped with a figure. Left bar group labeled "Finland" with figure "12 kg/person". Middle bar group labeled "Norway" with figure "10 kg/person". Right bar group labeled "Sweden" with figure "8 kg/person". Source citation at the bottom-left reads "Source: International Coffee Organization, 2025" in small grey text. Editorial illustration style.

**Tip:** for infographics with charts or graphs, Qwen 2.0 renders simple bar/line/pie charts well when you describe the data points concretely. Don't expect it to invent your data — describe what numbers go where.

---

## Pattern 5: Menu / Price List

Menus have a header, a list of items with prices, and often section breaks. Describe items in order.

**Template:**
> [Menu style and color palette]. Header reads "[RESTAURANT NAME]". Section header: "[SECTION]". Items listed: "[Item 1]" — "[price]", "[Item 2]" — "[price]", "[Item 3]" — "[price]". [Continue with sections]. Footer: "[footer text]".

**Example:**
> Elegant cafe menu, cream-colored paper background with a soft border. Header at the top reads "MILLIE'S COFFEE" in elegant serif. Below it, smaller text reads "Established 1952". First section header reads "ESPRESSO". Items listed under it: "Single Espresso" priced "$3.50", "Double Espresso" priced "$5", "Cortado" priced "$4.50". Second section header reads "POUR-OVER". Items listed: "Ethiopia Yirgacheffe" priced "$6", "Colombia Huila" priced "$5.50". Footer at the bottom reads "All beans roasted weekly on site". Hand-illustrated cup motif in the upper-right corner.

---

## Pattern 6: Book Cover

Book covers have a title, author, and often a tagline or genre indicator, with strong style anchor.

**Template:**
> [Book genre/style]. Title at [position] reads "[TITLE]" in [font]. [Cover art description]. Author name [position] reads "[AUTHOR]". [Optional tagline]: "[TAGLINE]".

**Example:**
> Minimalist literary fiction book cover, off-white background with a single small color image centered. Title in the upper third reads "The Lighthouse Keeper" in tall thin serif, italic. Centered cover art: a small ink illustration of a single lighthouse against a stormy sky. Author name at the bottom reads "Eleanor Marsh" in smaller matching serif. Above the author name, a slim tagline reads "A novel". Composition has generous white space.

---

## Pattern 7: Packaging / Product Label

Product labels balance brand name, product type, and required regulatory text.

**Template:**
> [Product type and shape]. Front of package: brand name "[BRAND]" in [font]. Below brand, product line reads "[PRODUCT]" in [font]. [Variant indicator]: "[VARIANT]". Bottom of label: "[volume/weight]". [Side panel content if applicable].

**Example:**
> Premium hot sauce bottle, glossy glass with a black cap, photographed on slate-grey backdrop. Front label is matte cream paper with red border. Brand name centered at the top reads "PEPPER ROAD" in bold western-style serif with weathered texture. Below it, smaller text reads "Small Batch Hot Sauce". A pepper illustration centered in the middle. Variant strip below the illustration reads "ORIGINAL HEAT". Bottom of the label reads "5 fl oz (148 ml)" with a slim ingredient line in tiny type below. Studio product photography, soft three-point lighting, slight reflection in the bottle.

---

## Pattern 8: Social Media Graphic

Social graphics emphasize bold typography over busy imagery, with a 1:1 or 9:16 aspect.

**Template:**
> [Graphic style and aspect ratio]. Primary text reads "[TEXT]" in [font]. [Visual element]. [Optional secondary text].

**Example:**
> Bold 1:1 social media quote graphic, deep navy background with a single yellow accent. Primary text fills the center of the frame and reads "Done is better than perfect" in large bold sans-serif. Below the quote, in much smaller text, an attribution reads "— Sheryl Sandberg". A tiny yellow underline runs beneath the attribution. Clean minimal composition.

---

## Pattern 9: Newspaper / Magazine Headline

Newspapers and magazine spreads layer headline, deck, byline, and body text with specific typographic conventions.

**Template:**
> [Publication style]. Main headline at the top reads "[HEADLINE]" in [font]. Deck/standfirst below reads "[DECK]" in [smaller font]. Byline reads "[BYLINE]". Body text in [column layout] reads "[first paragraph]".

**Example:**
> 1970s newspaper front page, slightly yellowed paper texture. Main headline across the top reads "ECONOMY GAINS GROUND" in massive bold serif, all caps. Deck below the headline reads "Manufacturing sector posts third quarter of growth as inflation eases" in lighter italic serif. Byline reads "By Margaret Holloway, Staff Reporter". Body text begins in three columns, the first column starts "WASHINGTON — Federal economists released figures Tuesday showing..." in classical newspaper-body serif. Period-accurate halftone photo to the right of the headline.

---

## Pattern 10: Bilingual / Multilingual Layout

When the image contains text in multiple languages, give each language its own quoted block. See `references/bilingual-and-multilingual.md` for deeper treatment.

**Template:**
> [Scene]. Primary text in [language 1] reads "[TEXT]" in [font]. Below it, [language 2] text reads "[TEXT]" in [font]. [Continue].

**Examples:**

*English + Chinese:*
> Minimalist movie poster, dark blue background with a city skyline silhouette. Big English title centered near the top reads "QUIET STREETS" in tall sans-serif. Smaller Chinese subtitle below it reads "静谧之城" in matching weight. Bottom of the poster reads "In theaters February 2026" in small English text, with Chinese release date "二月上映" alongside. Clean modern typography.

*English + Japanese:*
> Vintage Tokyo izakaya storefront at night. Lit paper lantern hangs by the door, Japanese text on the lantern reads "居酒屋". Above the door, an English chalkboard sign reads "TANAKA'S — Open Until 2 AM" in slightly uneven hand-written letters. Warm tungsten glow spilling onto the wet pavement, cinematic neon-lit night atmosphere.

*English + Spanish:*
> Bright market produce stand, hand-lettered sign at the top reads "Fresh Tomatoes" in bold red letters. Below it, in slightly smaller hand-lettering, reads "Tomates Frescos" in matching red. Small price card next to it reads "$3/lb · $6/kg". Sunlit outdoor market atmosphere.

---

## Common pitfalls and fixes

**Garbled text:**
- Raise guidance_scale to 5.0+
- Shorten the text — Qwen handles 1–8 word phrases more reliably than full sentences
- Front-load it earlier in the prompt
- Add "clean typography, sharp lettering" to the positive prompt
- Add "garbled text, misspelled text" to the negative prompt

**Wrong font:**
- Be more specific about the font style — "weathered hand-painted serif with chipped paint" beats "old-looking font"
- Reference real typographic eras — "art deco letterforms", "Bauhaus geometric sans"

**Text in wrong position:**
- Use explicit spatial language and be redundant if needed: "centered at the very top of the image, occupying the upper 20% of the frame"
- For tight constraints, describe the position twice in different ways

**Multi-line text breaks weirdly:**
- Either describe how it should break ("title on two lines, first line 'QUIET' second line 'STREETS'") or just use shorter text

**Numbers/dates rendered incorrectly:**
- Spell out short ones ("July fifteenth") if Qwen's having trouble, then go back to numerals once you've got the layout
- For prices, include the currency symbol explicitly: "$89" beats "89 dollars"

---

## When NOT to use Qwen for text

If the rest of the image is the priority and text is secondary, Flux 2 Pro/Max produces better non-text imagery. Qwen's edge is text-as-primary use cases. For a beautiful portrait that happens to have a small sign in the background, Flux is usually better. For a poster where the text IS the image, Qwen is the right tool.
