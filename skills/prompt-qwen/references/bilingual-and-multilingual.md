# Bilingual & Multilingual Text Patterns

Qwen Image renders Chinese characters as well as it renders English — better than any other major text-to-image model. This makes it the default choice for any work where Chinese text appears, and the only good choice when both English and Chinese appear together.

This reference covers patterns for Chinese-only, bilingual (Chinese + English most commonly), and multilingual layouts.

---

## Core principles

1. **Each language gets its own quoted block.** Don't mix scripts inside a single quote.
2. **Specify the script style for each language.** Chinese has multiple typographic traditions (kaiti, songti, heiti, brush calligraphy); English has its own. Name the style for each.
3. **Respect language-specific layout conventions.** Traditional Chinese typography reads top-to-bottom right-to-left; modern Chinese reads left-to-right like English. Specify which.
4. **For Chinese text, you can write the characters directly or use pinyin in parentheses if you want to be unambiguous.** Both work, but characters are more reliable.
5. **For mixed-language layouts, describe the visual hierarchy.** Which language is primary? Which is supporting?

---

## Chinese typography vocabulary

Naming the right Chinese typographic tradition gives Qwen the specific look you want.

| Style name (English / Chinese) | Look |
|---|---|
| **Kaiti / 楷体** | Standard regular script, balanced, used for body text |
| **Songti / 宋体** | Mincho-like serif, used for traditional books, newspapers |
| **Heiti / 黑体** | Bold modern sans-serif, used for headlines, posters |
| **Lishu / 隶书** | Clerical/official script, broad horizontal strokes, ancient feel |
| **Xingshu / 行书** | Semi-cursive running script, fluid, used for personal calligraphy |
| **Caoshu / 草书** | Fully cursive grass script, highly stylized, artistic only |
| **Zhuanwen / 篆文** | Seal script, ancient archaic style, used for stamps and seals |
| **Brush calligraphy / 毛笔书法** | Traditional ink brush look with visible brush variation |
| **Hand-painted / 手绘** | Casual brush lettering, signage style |
| **Modern simplified / 简体** | Mainland China standard character set |
| **Traditional / 繁体** | Hong Kong, Taiwan, classical texts |

---

## Pattern 1: Chinese-only signage

**Template:**
> [Scene]. [Sign type and placement] reads "[CHINESE TEXT]" in [Chinese script style].

**Example:**
> Traditional Beijing hutong courtyard entrance, weathered red wooden door with brass studs. A vertical wooden plaque hanging beside the door reads "茶馆" in classical brush calligraphy, deep black ink on aged wood. Late afternoon sunlight catching the door's iron handle, quiet courtyard atmosphere.

**Note:** Vertical Chinese text reads top-to-bottom. Specify "vertical" or "horizontal" so Qwen knows the orientation.

---

## Pattern 2: English + Chinese bilingual

This is the most common pattern. Typically English is primary, Chinese supporting, or vice versa.

**Template (English primary):**
> [Scene]. Main text reads "[ENGLISH]" in [English font style]. Below it, smaller Chinese text reads "[中文]" in [Chinese script style].

**Template (Chinese primary):**
> [Scene]. Main text reads "[中文]" in [Chinese script style]. Below it, smaller English translation reads "[ENGLISH]" in [English font style].

**Examples:**

*English-primary movie poster:*
> Minimalist movie poster, dark blue background with a city skyline silhouette. Large English title centered near the top reads "QUIET STREETS" in tall thin sans-serif. Smaller Chinese subtitle directly below reads "静谧之城" in matching weight modern heiti. At the bottom, English release date reads "February 2026" with Chinese release date "二月上映" alongside in the same size. Clean modern typography, balanced composition.

*Chinese-primary tea shop:*
> Hand-painted wooden sign over a tea shop entrance. Main text in the center reads "明月茶舍" in elegant brush calligraphy, deep ink on cream background, with visible brush variation. Below the Chinese, smaller English text reads "Bright Moon Teahouse" in a simple complementary serif. Warm side lighting, traditional courtyard atmosphere.

*Restaurant menu header:*
> Elegant restaurant menu header. Large English text reads "DUMPLING HOUSE" in bold modern sans-serif. Directly below it, in matching weight, Chinese text reads "饺子馆" in modern heiti. A small decorative line separates the header from the menu items. Cream paper background, professional restaurant menu design.

*Storefront with traditional + modern:*
> Hong Kong street-level shopfront at dusk, neon and signage layered. Large neon Chinese text reads "金龍酒家" in traditional characters, glowing red and gold. Below it, an English subtitle on a smaller painted sign reads "Golden Dragon Restaurant" in art-deco serif. Rain-slicked street, classic Wong Kar-wai color palette.

---

## Pattern 3: Trilingual / multilingual

Tourist locations, international brands, and product packaging often need three or more languages.

**Example:**
> Multilingual airport directional signage. Main word at the top reads "ARRIVALS" in bold blue sans-serif. Below it, three translations stacked vertically: "到达" in modern Chinese heiti, "到着" in Japanese gothic, and "도착" in Korean dotum. Each translation in matching weight, smaller than the English. Below all four, a directional arrow points right. Modern airport interior, clean institutional design.

For more than three languages, group them visually and describe the grouping:

> European product packaging, ingredient list with translations in five languages arranged in a grid. Top row in English reads "Ingredients: Water, Salt, Sugar". Below it, the same in French: "Ingrédients: Eau, Sel, Sucre". Below that, German: "Zutaten: Wasser, Salz, Zucker". Italian: "Ingredienti: Acqua, Sale, Zucchero". Spanish: "Ingredientes: Agua, Sal, Azúcar". All in the same small sans-serif font, equal visual weight, label-typography style.

---

## Pattern 4: Cultural-specific Chinese typography

Some Chinese contexts have strong typographic conventions worth naming:

*Traditional couplet (春联):*
> Lunar New Year doorway with traditional red paper couplets flanking a red wooden door. Right couplet reads "福满人间" vertically in bold gold brush calligraphy. Left couplet reads "春回大地" vertically in matching style. Above the door, a horizontal banner reads "万事如意" in the same gold brush style. All three printed on bright red paper. Festive new-year atmosphere, snow on the ground.

*Storefront signage (招牌):*
> Vintage 1980s Hong Kong storefront, large wooden signboard mounted above the entrance. Sign reads "永福茶餐廳" in traditional characters, deep gold lacquered brush calligraphy on a deep red wooden plaque. Below it, in much smaller English, reads "Wing Fook Cha Chaan Teng" in modest serif. Neon details to either side, classic dai pai dong street atmosphere.

*Calligraphy scroll (字画):*
> Traditional Chinese hanging scroll on a pale silk mounting, displayed on a plain wooden wall. The scroll contains a single column of four large characters: "山高水长" rendered in flowing xingshu running script, dark ink with visible brush variation. Below the calligraphy, a small red seal stamp shaped as a square. Soft museum-style lighting, contemplative atmosphere.

*Seal stamp (印章):*
> Close-up of a traditional Chinese seal pressed into red cinnabar paste on rice paper. The seal reads "明月山房" in archaic zhuanwen seal script, blocky and geometric. Sharp edge detail, slight ink bleed at the edges of the impression, white rice paper background.

---

## Pattern 5: Mixed scripts in a single design

Some modern Chinese design uses both Chinese and Latin characters together for stylistic effect.

**Example:**
> Modern Chinese coffee shop branding. Logo combines Chinese and English: large Chinese text "明日咖啡" in geometric modern heiti dominates the upper half. Directly below, the same brand name in English "Tomorrow Coffee" in a matching weight modern sans-serif, slightly smaller. Both share the same forest-green color. Below the wordmark, a tagline in small italic English reads "Roasted today, sipped tomorrow". Clean minimalist composition on cream background.

---

## Japanese-specific notes

Qwen also handles Japanese, though slightly less reliably than Chinese.

- **Hiragana / Katakana / Kanji** can all be specified — name them explicitly: "katakana script for the brand name, kanji for the descriptive subtitle"
- **Vertical writing (縦書き)** is common in Japanese; specify when desired
- **Common typographic traditions:** *Mincho* (serif-like, traditional), *Gothic* (sans-serif, modern), *Brush* (毛筆体)

**Example:**
> Tokyo back-alley izakaya storefront at night. Paper lantern hanging by the door, Japanese hiragana on the lantern reads "いらっしゃい" in brush-style hand lettering. Above the door, a small wooden plaque in kanji reads "田中酒場" in traditional sumi ink. Warm tungsten light spilling onto wet pavement, cinematic atmosphere.

---

## Korean-specific notes

Hangul is well-rendered by Qwen. Common scripts:

- **Myeongjo (명조)** — serif-like, traditional, for body text
- **Gothic / Dotum (고딕 / 돋움)** — sans-serif, modern, for headlines
- **Brush (붓글씨)** — calligraphic, decorative

**Example:**
> Korean street market scene, hand-painted sign over a food stall reads "떡볶이" in bold red brush-style hangul. Smaller subtitle below reads "전통 매운맛" in matching style. Steam rising from a metal pan, evening atmosphere with practical lighting from nearby vendors.

---

## Pitfalls and fixes

**Wrong characters rendered:**
- Spell-check the source text carefully
- For uncommon characters, lean on guidance_scale: 5.0
- Avoid extremely rare characters; Qwen's training is heaviest on common modern usage

**Characters look stylistically wrong:**
- Be more specific about the script tradition (kaiti vs heiti vs xingshu)
- Reference a specific era ("Song Dynasty calligraphy", "1980s Hong Kong neon signage")

**Characters bleed into background:**
- Specify "clean lettering, sharp edges, high contrast against background"
- Choose a background color that contrasts strongly

**Wrong character variant (simplified vs traditional):**
- State explicitly: "simplified Chinese" or "traditional characters"
- For specific regions: "Mainland Chinese simplified", "Taiwanese traditional", "Hong Kong traditional"

**Mixed languages overlap or compete visually:**
- Make the visual hierarchy explicit: "Chinese is primary, English is supporting and 60% the size of the Chinese"
- Specify spacing: "with clear separation between the two language blocks"

---

## Parameter notes

For bilingual/multilingual work, push guidance higher:
- `guidance_scale: 5.0` for reliable multi-script rendering
- `num_inference_steps: 35–50`

The added complexity of correctly rendering two character systems benefits from more inference compute.
