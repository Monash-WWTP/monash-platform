---
name: Monash Water public portal
description: Practical public information and Android app distribution.
colors:
  ink: "#202724"
  muted: "#58635d"
  rule: "#dbe2dd"
  green: "#146346"
  green-hover: "#0c4d35"
  soft: "#f2f6f3"
  white: "#fff"
typography:
  display:
    fontFamily: "Manrope, sans-serif"
    fontSize: "clamp(36px,4vw,52px)"
    fontWeight: 650
    lineHeight: 1.18
    letterSpacing: "-0.035em"
  page-title:
    fontFamily: "Manrope, sans-serif"
    fontSize: "42px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Manrope, sans-serif"
    fontSize: "29px"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Manrope, sans-serif"
    fontSize: "15px"
    lineHeight: 1.65
  compact:
    fontFamily: "Manrope, sans-serif"
    fontSize: "13px"
    lineHeight: 1.65
rounded:
  control: "8px"
  band: "12px"
  card: "14px"
spacing:
  inline: "10px"
  compact: "18px"
  row: "24px"
  group: "30px"
  columns: "36px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "14px 25px"
  button-primary-hover:
    backgroundColor: "{colors.green-hover}"
  button-text:
    textColor: "{colors.green}"
    padding: "8px 0"
  account-link:
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 17px"
  app-card:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "36px 27px"
---

# Design System: Monash Water public portal

## Overview

**Creative North Star: "Practical app listing"**

Monash Water’s public portal uses the user-approved practical app listing: white ground, charcoal text and deep green actions. Self-hosted Manrope, clear heading sizes and generous section spacing make download instructions and public reading straightforward.

This records the public portal only. Actual app imagery represents the published Android release with a release-specific caption. Shared account copy distinguishes local staging from the legacy public APK before account actions.

**Key Characteristics:**

- White, charcoal and deep green
- Self-hosted Manrope hierarchy
- Flat surfaces and thin dividers
- Rounded rectangular actions
- Visible keyboard focus

## Colors

Deep green is the single interface accent against a white ground. The frontmatter owns canonical values.

### Primary

Deep green marks primary actions, links, installation step numbers and keyboard focus. Its deeper hover state confirms primary action interaction.

### Neutral

Charcoal carries headings and navigation; muted gray-green carries supporting prose and metadata. Pale green surfaces group app and account information. Light gray-green rules divide sections and release disclosures.

**The Action Color Rule.** Use deep green to identify actions and focus consistently.

## Typography

Self-hosted Manrope has a sans-serif fallback and variable weights (200–800). Headings use (650), buttons (700), navigation (600). Size differences establish hierarchy.

The display role is the desktop home heading; mobile uses (35px). Page titles reduce to (33px) for the app and (32px) for reading pages. Installation headlines reduce to (27px). App summary text uses (26px), weight (550), line height (1.4), reducing to (23px). Reading introductions use (19px), reducing to (17px). Reading paragraphs use the body role; supporting copy usually uses compact type and muted color. Navigation uses (13px), reducing to (12px). Release values use tabular numerals.

**The Direct Heading Rule.** Let a meaningful heading establish each section without an ornamental label above it.

## Layout

Home and download content center in a maximum (1280px) container with (6%) gutters and bottom padding (72px). The header uses maximum (1440px), minimum height (84px), and horizontal navigation. Reading content centers within (840px) with padding (65px 30px 80px); paragraphs cap at (70ch).

The download hero uses weighted columns (1.25fr / .75fr), gap (80px), and padding (48px 0 66px). The screenshot is (234px) wide and follows download copy in DOM order. Installation instructions and platform paths use three columns with (36px) gaps. At (900px), gutters become (5%) and gaps tighten. At (640px), grids stack, navigation wraps, the screenshot is (190px), and the download action spans its container. Reading padding becomes (38px 5% 60px).

## Elevation & Depth

No cast shadows appear in public CSS. White space, pale tonal fills and thin divider strokes separate information. Native app pixels retain their own visual language inside the screenshot.

**The Flat Surfaces Rule.** Use tonal fills and thin rules to separate public surfaces.

## Shapes

Actions and outlined account navigation use the control radius. App cards and account bands use the larger radii in frontmatter. Numbered installation markers use (7px) rounding. The screenshot frame uses (23px) rounding and a (1px) rule border. App icons retain rounded silhouettes.

## Components

### Buttons

The primary action is a deep green rounded rectangle with white text, (15px) type and weight (700), minimum height (54px). Hover deepens the fill through a (.18s ease) background transition. Disabled controls use opacity (.55). Copy actions are transparent green text buttons with (12px) type and weight (650). Text actions underline on hover.

All public interactive controls retain a green (3px) focus outline offset (4px). Reduced motion removes transitions and smooth scrolling.

### Cards / Containers

The home app card groups an icon and stacked text with a pale fill, no border or shadow. The account band uses the same tonal grouping, padding (28px 30px), band radius, and stacks on mobile. Release facts are a semantic definition list between thin rules. Native details/summary disclosures use bottom rules and compact copy.

### Navigation

The brand uses (22px), weight (750) and tracking (-.035em); mobile uses (21px). Navigation has a (27px) gap, reducing to (18px) on mobile. Links are charcoal at rest, green and underlined on hover. The account link uses a light outline. A focusable skip link appears at the top when focused.

### Published app preview

The image is an actual published report screen. Its caption identifies the Android release. Release size, version, platform requirement and checksum come from the release record.

### Account continuation

Account pages present scope and current release limitations before the primary continuation link. These links enter identity routes; no embedded credential field primitive is established by these pages.

## Do's and Don'ts

### Do:

- Do use deep green for primary actions and links.
- Do tie release facts and screenshot captions to the actual published artifact.
- Do explain account scope before the account action.
- Do preserve visible keyboard focus and reduced motion.

### Don't:

- Don't add decorative eyebrows above headings.
- Don't invent release metrics, research results or institutional endorsements.
- Don't imply the public legacy APK already uses the local shared identity service.
