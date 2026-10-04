---
name: Python from zero
description: A sunlit research desk for learning Python from the first line, adapted from the Heptabase visual world.
colors:
  eggshell-canvas: "#fdfcfb"
  cloud-surface: "#f7f7f7"
  paper-beige: "#f0f0ea"
  whiteboard-gray: "#eeeded"
  linen-border: "#e4ded3"
  hairline: "rgba(0, 0, 0, 0.08)"
  tool-edge: "rgba(0, 0, 0, 0.13)"
  graphite: "#2e2e2e"
  charcoal-copy: "#454545"
  quiet-gray: "#6a6972"
  disabled-ash: "#a8a8a8"
  research-blue: "#207dff"
  ember: "#b4462a"
typography:
  display:
    fontFamily: "Instrument Sans, DM Sans, Arial, sans-serif"
    fontSize: "48px"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "-1.58px"
  headline:
    fontFamily: "Instrument Sans, DM Sans, Arial, sans-serif"
    fontSize: "36px"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "-0.54px"
  title:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 500
    lineHeight: 1.5
  body:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.6
    fontFeature: "\"cv11\", \"ss01\""
  body-lead:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: "27px"
  body-compact:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  button:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: "20px"
  label:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1
  label-small:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.5
  badge:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 600
  wordmark:
    fontFamily: "Inter, Arial, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    letterSpacing: "-0.36px"
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Consolas, Liberation Mono, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  inline: "4px"
  control: "6px"
  feature: "8px"
  card: "12px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  base: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
  section-gap-phone: "80px"
  section-gap: "128px"
  first-section: "48px"
  page-gutter: "16px"
  measure: "42rem"
  wide: "54rem"
components:
  topbar:
    backgroundColor: "{colors.eggshell-canvas}"
    textColor: "{colors.graphite}"
    height: "72px"
    padding: "0 24px"
  link:
    textColor: "{colors.research-blue}"
  button-primary:
    backgroundColor: "{colors.graphite}"
    textColor: "#ffffff"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: "7px 22px"
  button-primary-hover:
    backgroundColor: "#1f1f1f"
  button-tool:
    backgroundColor: "transparent"
    textColor: "{colors.graphite}"
    rounded: "{rounded.control}"
    padding: "6px 10px 6px 12px"
  button-tool-hover:
    backgroundColor: "{colors.cloud-surface}"
  badge:
    backgroundColor: "{colors.eggshell-canvas}"
    textColor: "{colors.charcoal-copy}"
    typography: "{typography.badge}"
    rounded: "{rounded.control}"
    padding: "6px 12px"
  switcher:
    backgroundColor: "{colors.cloud-surface}"
    rounded: "{rounded.pill}"
    padding: "3px"
  switcher-segment:
    textColor: "{colors.quiet-gray}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "8px 14px"
  switcher-segment-active:
    backgroundColor: "{colors.eggshell-canvas}"
    textColor: "{colors.graphite}"
  card:
    backgroundColor: "{colors.eggshell-canvas}"
    rounded: "{rounded.card}"
    padding: "24px"
  card-on-cloud:
    backgroundColor: "{colors.cloud-surface}"
    rounded: "{rounded.card}"
    padding: "24px"
  words-box:
    backgroundColor: "{colors.paper-beige}"
    textColor: "{colors.charcoal-copy}"
    rounded: "{rounded.feature}"
    padding: "16px 17px"
  whiteboard-canvas:
    backgroundColor: "{colors.whiteboard-gray}"
    rounded: "{rounded.card}"
    padding: "28px"
    width: "{spacing.wide}"
  window:
    backgroundColor: "{colors.eggshell-canvas}"
    textColor: "{colors.graphite}"
    rounded: "{rounded.card}"
    width: "{spacing.measure}"
  window-titlebar:
    textColor: "{colors.quiet-gray}"
    height: "40px"
    padding: "10px 14px 10px 16px"
  window-output:
    backgroundColor: "{colors.cloud-surface}"
    textColor: "{colors.charcoal-copy}"
    typography: "{typography.code}"
    padding: "12px 16px"
  quiz-option:
    backgroundColor: "{colors.eggshell-canvas}"
    textColor: "{colors.graphite}"
    typography: "{typography.body-compact}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  quiz-option-hover:
    backgroundColor: "{colors.cloud-surface}"
  quiz-option-wrong:
    textColor: "{colors.disabled-ash}"
  code-inline:
    backgroundColor: "{colors.cloud-surface}"
    rounded: "{rounded.inline}"
    padding: "0.05em 0.35em"
---

# Design System: Python from zero

## Overview

**Creative North Star: "The Sunlit Research Desk"**

A lesson is a research desk, not a course dashboard. Reading happens on a warm eggshell page in a single centred column; doing happens inside floating research windows set on a whiteboard-gray canvas, the same place Heptabase puts its product demos. The page is type-led and sparse: Instrument Sans headlines carry quiet weight, Inter carries everything a learner reads and touches, and monospace appears only where Python is.

The world is pinned, not invented. It is Heptabase as read by Refero (`design_system/heptabase-reference.md`), adapted from a marketing page to a Read-mode lesson. The adaptation keeps Heptabase's surfaces, ink, type pairing, radii and elevation intact and extends it in six places: a 17px reading body for long study sessions, a 15px compact step for dense teaching material, an Ember failure colour for Python's own errors, the exercise window, the anatomy figure, and a section rhythm that drops from 128px to 80px on phones with the first section only 48px below the switcher. Elements of the source that this build does not use (the Large Workspace Overlay shadow, the translucent workspace card, the 44px display step, Inter 700) are not part of this system until a surface needs them.

Density is calm and compact: a 4px base unit, 8px between sibling controls, generous air between ideas. Surfaces are flat and separated by tone or a 1px hairline. The only thing that floats is a window, because a window is where work happens.

**Key Characteristics:**
- Warm off-white page, never pure white.
- One reading column (42rem) with figures and canvases breaking out to 54rem.
- Charcoal pills act; outlined 6px tools assist; Research Blue only points.
- Flat cards and paper boxes; a soft three-layer shadow reserved for windows.
- Monospace means Python: code, filenames, and console output, nothing else.

## Colors

Warm, low-chroma neutrals carry the whole page; two saturated colours exist and each has exactly one job.

### Primary
- **Graphite** (#2e2e2e): primary text, headings, the filled primary pill, the wordmark tile, the active switcher segment's text, and the correct quiz option's outline. It is the system's action colour as well as its ink, which keeps actions serious rather than loud.

### Secondary
- **Research Blue** (#207dff): links, the focus ring, the editor caret, the editor's inset focus glow (at 35% alpha), text selection (at 16% alpha), the Solved status dot, passing-test dots, the tick on a correct quiz answer, and the string token in the anatomy figure. Always a small mark or a line of text, never a filled area.

### Tertiary
- **Ember** (#b4462a): a build extension with no Heptabase counterpart. Used only for Python's error lines and failing-test labels inside window output, plus the hollow ring that marks a failing test. Chosen as a muted brick so a mistake reads as information, not alarm, in line with "mistakes are part of the lesson".

### Neutral
- **Eggshell Canvas** (#fdfcfb): page background, top bar, cards, windows, the editor, badges, quiz options, the active switcher thumb.
- **Cloud Surface** (#f7f7f7): switcher track, window output and console panes, inline code chips, hover fill for tools and quiz options, the "on cloud" card variant.
- **Paper Beige** (#f0f0ea): the "New words" box and the highlight on a targeted source note.
- **Whiteboard Gray** (#eeeded): the canvas behind every window, figure and exercise.
- **Linen Border** (#e4ded3): outline badges, and the window border in print.
- **Hairline** (rgba(0, 0, 0, 0.08)): every structural divider: titlebar and toolbar rules, output pane tops, table rows, card edges, the pager rule, the switcher track edge.
- **Tool Edge** (rgba(0, 0, 0, 0.13)): outlines on tool buttons, quiz options and keycaps; slightly firmer than a hairline because it marks something pressable.
- **Charcoal Copy** (#454545): secondary text: intros, output text, "New words" definitions, anatomy labels, sources.
- **Quiet Gray** (#6a6972): helper copy, the top bar's location line, inactive switcher segments, titlebar status, output labels, table headers, figure captions, hint summaries.
- **Disabled Ash** (#a8a8a8): the unchecked status dot, anatomy brackets and leader lines, struck-through wrong quiz answers, scrollbar thumbs.

### Named Rules
**The Blue Points Rule.** Research Blue marks where to go or what just succeeded: a link, a focus ring, a caret, a dot. It never fills a button, a card, or a band.

**The Ember Speaks Only for Python Rule.** Ember appears only inside a window's output, on lines Python or the tests produced. Lesson copy, warnings, and UI chrome never use it.

**The No Pure White Rule.** The canvas is Eggshell. Pure white (#ffffff) appears only as the label on the Graphite pill and as the print background.

## Typography

**Display Font:** Instrument Sans 500 (with DM Sans, Arial)
**Body Font:** Inter 400, 500, 600 (with Arial), with character variants cv11 and ss01 on
**Label/Mono Font:** ui-monospace (with SFMono-Regular, Consolas, Liberation Mono)

**Character:** A humanist display face with tight negative tracking gives headlines a quiet, bookish confidence; Inter does all the reading and all the interface work so the page never feels like two products stitched together.

### Hierarchy
- **Display** (500, 48px, 1.3, -1.58px tracking): the page title in the centred hero, balanced, capped at 14em. Drops to 36px with -0.54px tracking below 640px.
- **Headline** (500, 36px, 1.3, -0.54px): one per section, left-aligned, balanced. Drops to 30px below 640px.
- **Title** (Inter 500, 20px, 1.5): sub-steps inside a section, exercise titles, card headings. Sits 48px below the text above it.
- **Body** (Inter 400, 17px, 1.6): all lesson prose, in a 42rem column (about 70 characters). A build extension: Heptabase's body is 16/1.5, raised here for sustained study.
- **Body Lead** (Inter 400, 18px, 27px): the hero intro only, Charcoal Copy, max 34rem. 17px at 1.55 on phones.
- **Body Compact** (Inter 400, 15px, 1.5): "New words" lists, tables, quiz options and feedback, hints, the pager. A build extension between Heptabase's 14 and 16.
- **Caption** (Inter 400, 14px, 1.5): side notes, figure captions, sources, the top bar location line.
- **Button** (Inter 500, 15px, 20px): pill and tool button labels; tool buttons set 14px.
- **Label** (Inter 500, 13px): switcher segments and window titlebar status.
- **Label Small** (Inter 500, 12px): output pane labels ("Shows", "Your code printed", "Tests") and table headers. Badges use 12px at 600.
- **Code** (ui-monospace 400, 14px, 1.6): code blocks, the editor, filenames (13px), console output (13.5px), inline code at 0.86em. The anatomy figure sets a single line at 34px (22px on phones).

### Named Rules
**The 500 Ceiling Rule.** Instrument Sans is never heavier than 500. Emphasis inside body copy uses Inter 600, never a heavier display weight.

**The Monospace Means Python Rule.** Monospace is reserved for Python code, file names, and what Python printed. Labels inside output panes switch back to Inter so the learner can tell the page's voice from Python's.

## Layout

A single centred reading column (42rem) inside a 16px page gutter, with a 72px top bar (60px on phones) whose content is capped at 76rem. Whiteboard canvases, figures and side-by-side code pairs break out to 54rem; windows inside them return to 42rem so code lines up with the prose above. Reference sheets use an auto-fit card grid (19rem minimum, 60rem cap).

Section rhythm is set by the section gap: 128px between major parts, reduced to 80px below 640px. The first section sits 48px below the sticky switcher so the opening heading lands in the first viewport. Inside a section: 16px after paragraphs and headline, 48px before a title, 24px around boxes and cards, 32px around canvases, 64px above the pager.

The pill switcher is sticky 12px from the top and centred, so wayfinding follows the reader without a sidebar. Anchor jumps leave 88px of scroll padding for it.

Responsive changes, observed in the build: below 640px the section gap, top bar, hero and headline sizes shrink, code pairs stack, canvases tighten to 16px by 12px padding and bleed 4px into the gutter, and switcher segments narrow to 10px side padding. Below 560px quiz options stack and the anatomy figure re-sets at 22px with wrapping labels. Below 520px "New words" definitions stack under their terms.

### Named Rules
**The Read on Eggshell, Do on Whiteboard Rule.** Explanation lives in the column on the page. Anything the learner runs, inspects or edits sits in a window on a Whiteboard canvas.

## Elevation & Depth

The system is flat by default and conveys depth through tone: Eggshell on Whiteboard, Cloud panes inside Eggshell windows, Paper boxes inside the column. Shadows exist only to say "this is a separate object you can work in".

### Shadow Vocabulary
- **Floating Window** (`box-shadow: 0 0 4px rgba(0,0,0,0.03), 0 4px 8px rgba(0,0,0,0.04), 0 16px 26px rgba(0,0,0,0.05)`): every window on a Whiteboard canvas. Removed in print and replaced with a Linen Border outline.
- **Pill Lift** (`box-shadow: 0 1px 2px rgba(0,0,0,0.05)`): the switcher track; the active thumb adds a 1px hairline ring to it.

### Named Rules
**The Only Windows Float Rule.** Cards, paper boxes, badges and buttons are flat. If something needs a shadow, it should be a window.

## Shapes

Soft, consistent corners on a fixed ladder: 4px for inline chips (code, keycaps, a highlighted source), 6px for controls (tool buttons, badges, quiz options), 8px for the paper feature box, 12px for cards, canvases and windows, and full pills for the primary action and the switcher. Links have no shape. Borders are 1px hairlines or tool edges; the only heavier strokes are the 2px keycap bottom and the 1.5px anatomy brackets. Status is shown with 7px dots: filled Ash for unchecked, filled Blue (scaled 1.25) for solved and passing, a hollow Ember ring for failing.

### Named Rules
**The Pill Acts, the Rectangle Assists Rule.** The one primary action in a context is a Graphite pill. Secondary actions are 6px outlined tools. Never a 6px rectangle for the primary action.

## Components

### Buttons
Quiet and decisive: one dark pill per context, everything else outlined and light.
- **Shape:** full pill for primary (9999px); gently rounded for tools (6px).
- **Primary:** Graphite fill, white label, Inter 500 15px, 7px by 22px padding. Used for Check in exercises and Start Lesson 1 on the home page.
- **Hover / Focus:** primary darkens to #1f1f1f; tools fill with Cloud Surface. Both transition background in 0.15s. Focus is the global 2px Research Blue outline with 2px offset. Disabled drops to 45% opacity with a progress cursor while Python runs.
- **Tool:** transparent, 1px Tool Edge outline, Graphite text at 14px, 6px by 10px by 6px by 12px padding, 14px outline icon with a 6px gap. Used for Run and Reset.

### Chips (outline badges)
- **Style:** Eggshell, 1px Linen Border, 6px corners, 6px by 12px padding, Inter 12/600 Charcoal Copy, optional 14px Quiet Gray outline icon.
- **State:** static. Badges state facts about the page (time, what you need). They never show progress, scores or achievement.

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** Eggshell with a 1px hairline edge; the "on cloud" variant is Cloud Surface with no visible edge, used for the task the learner does away from the page and for the reference link on home.
- **Shadow Strategy:** none (see Elevation).
- **Internal Padding:** 24px (20px in the reference grid).
- **Paper feature box ("New words"):** Paper Beige, 8px corners, 16px by 17px padding, Charcoal Copy text, a 14px/600 Graphite title, and a two-column term and definition grid at 15px.

### Inputs / Fields
- **Style:** the code editor is a borderless Eggshell textarea inside a window, monospace 14/1.6, 16px padding, 4-space tabs, vertical resize, Research Blue caret.
- **Focus:** no outline; an inset 2px Research Blue glow at 35% alpha.
- **Behaviour:** Tab and Shift+Tab indent, Enter keeps indentation, Escape leaves the editor, Ctrl+Enter checks.

### Navigation
- **Top bar:** 72px Eggshell bar, wordmark left (24px Graphite tile with an Eggshell prompt glyph, Inter 18/600, -0.36px), location and Reference link right in 14px Quiet Gray, darkening to Graphite on hover. 60px tall on phones, where the long location text is hidden.
- **Pill segmented switcher:** sticky, centred. Cloud track with a hairline edge and Pill Lift, 3px inner padding, 2px between segments. Segments are Inter 13/500 Quiet Gray; the one in view turns Graphite and an Eggshell thumb slides behind it (0.35s, ease-out). Segments name the lesson's topics followed by Check and Next.
- **Pager:** a hairline rule 64px below the content, two Graphite 500 links (Quiet 400 lead-in), turning Research Blue on hover.

### Exercise Window (signature)
The build's main extension to the world: a Heptabase floating preview that holds real, runnable Python.
- **Structure:** Whiteboard canvas (28px padding, 12px corners) with the task text above in the column width, then a floating window: titlebar (monospace filename left, status right), editor, toolbar (Check pill, Run and Reset tools, a 13px Quiet status line), and a console pane that appears after the first run.
- **Console:** Cloud Surface, monospace 13.5/1.6, Charcoal text; Inter 12/500 Quiet labels split printed output from test results. Passing tests are Graphite with a Blue dot; failing tests are Ember with a hollow Ember ring and Quiet detail lines; error tracebacks are Ember.
- **Solved moment:** when every test passes, the titlebar status dot eases from Ash to Research Blue and scales to 1.25 over 0.5s, and the label turns Graphite and reads "Solved". It happens once per pass, with no confetti or banner.
- **Static pairs:** read-only windows use the same frame with a code block and a Cloud "Shows" pane; two sit side by side on wide screens and stack below 640px.

### Anatomy Figure (signature)
A build extension for teaching syntax: one line of code set large in a window (monospace 34px), with each part bracketed underneath in 1.5px Ash and connected by a leader line to an Inter 14px Charcoal label, its token in Graphite 600. Strings take Research Blue. Labels stagger downward in 30px rows (46px on phones) so none overlap. A centred 14px Quiet caption sits below.

### Quiz
Options are Eggshell 6px tiles with a Tool Edge outline, Inter 15/1.4, in a two-column grid (one column below 560px). Hover fills Cloud. The correct pick gains a Graphite outline and a Research Blue tick; wrong picks turn Ash, struck through, and disable. Feedback is a 15px line below, never coloured red.

## Do's and Don'ts

### Do:
- **Do** set every page on Eggshell Canvas (#fdfcfb) and separate light surfaces with a 1px hairline (rgba(0, 0, 0, 0.08)) or a tonal step, not borders in colour.
- **Do** put anything runnable or inspectable in a floating window on a Whiteboard canvas, with the filename in the titlebar.
- **Do** keep reading text in the 42rem column at 17px/1.6, and break figures out to 54rem.
- **Do** use one Graphite pill per context for the primary action and 6px outlined tools for the rest.
- **Do** keep the section gap at 128px on desktop and 80px below 640px, with the first section 48px under the switcher.
- **Do** define every new word in a Paper Beige "New words" box the first time it appears.

### Don't:
- **Don't** fill a button or a surface with Research Blue.
- **Don't** use Ember outside window output, and don't use it for UI warnings or emphasis.
- **Don't** set Instrument Sans heavier than 500.
- **Don't** add shadows to cards, paper boxes, badges or buttons.
- **Don't** use a 6px rectangle for the primary action.
- **Don't** use pure white as the page canvas or gradients on page surfaces.
- **Don't** add progress bars, scores, streaks or achievement badges; outline badges carry facts only.
- **Don't** add coloured stripe callouts; a definition goes in the Paper box, a task goes on the Whiteboard.
