---
name: Public water atlas
description: Editorial public water information with distinct evidence classes.
colors:
  paper: "#f2f1e9"
  ink: "#0a2230"
  rule: "#b5c0be"
  link: "#155b80"
  surface: "#f7f6ee"
  release: "#b5715e"
  release-text: "#fff8ed"
  focus: "#b55336"
  citizen: "#246391"
  laboratory: "#2b766d"
  model: "#b3593d"
  citizen-soft: "#dce7f0"
  laboratory-soft: "#dce9e2"
  model-soft: "#f0dfd7"
typography:
  display:
    fontFamily: "Gelasio, Georgia, serif"
    fontSize: "62px"
    fontWeight: 400
    lineHeight: 1.035
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Gelasio, Georgia, serif"
    fontSize: "36px"
    fontWeight: 400
    lineHeight: 1.2
  title:
    fontFamily: "Gelasio, Georgia, serif"
    fontSize: "21px"
    fontWeight: 400
  body:
    fontFamily: "Gelasio, Georgia, serif"
    fontSize: "17px"
    lineHeight: 1.7
  label:
    fontFamily: "Gelasio, Georgia, serif"
    fontSize: "14px"
    lineHeight: 1.4
rounded:
  account: "2px"
  release: "3px"
  evidence: "50%"
spacing:
  icon-gap: "8px"
  compact: "12px"
  row: "22px"
  section: "28px"
components:
  button-release:
    backgroundColor: "{colors.release}"
    textColor: "{colors.release-text}"
    rounded: "{rounded.release}"
    padding: "0 24px"
    height: "52px"
  button-copy:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    padding: "12px 18px"
  account-link:
    textColor: "{colors.ink}"
    rounded: "{rounded.account}"
    padding: "9px 27px"
  atlas-control:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    width: "36px"
    height: "36px"
  purpose-panel:
    backgroundColor: "#f7f6eede"
    padding: "10px 22px 4px"
---

# Design System: Public water atlas

## Overview

**Creative North Star: "Public water atlas"**

The public water atlas pairs explicitly illustrative cartography with the calm reading rhythm of an academic publication. Warm paper, dark marine ink and Gelasio serif text give public instructions and research a coherent editorial voice.

Labelled community, laboratory and model treatments keep evidence visibly distinct. Public reading pages reuse that voice through generous margins, restrained rules and readable prose. This system records the public portal; the operator dashboard has a separate incumbent interface.

**Key Characteristics:**
- Warm paper and marine ink
- Editorial serif hierarchy
- Labelled evidence colors
- Flat ruled surfaces
- Visible keyboard focus

## Colors

The palette combines warm paper and marine ink with modest clay, blue and teal accents. Frontmatter is the normative source.

### Primary

Marine link blue identifies text links. Clay release color marks the Android action, and stronger clay focus makes keyboard location visible.

### Secondary

Citizen blue accompanies community observations; laboratory teal accompanies measurements; model clay accompanies illustrative outputs. Their pale companions fill evidence illustration circles.

### Neutral

Paper is the page ground, surface the lighter header ground, ink the text color and rule the divider color.

**The Evidence Labels Rule.** Color accompanies a text label; community observations, laboratory measurements and illustrative model outputs remain distinct.

## Typography

Locally served Gelasio uses Georgia and serif fallbacks. Regular serif headings establish hierarchy by size. Semibold is reserved for brand identity and concise emphasis.

The display role reduces to a fluid size (32–48px) and line height (1.1) below the narrow breakpoint. Section headlines reduce to (29px); evidence titles reduce to (19px). Reading-page titles use fluid sizing (34–52px), line height (1.15) and a maximum width (22ch). Reading prose uses the body role and a maximum paragraph width (70ch), reducing to (16px) on mobile. Reading introductions use (21px), reducing to (18px). Compact descriptions and navigation use the label role.

**The Editorial Hierarchy Rule.** Use regular serif headings and size to establish hierarchy; reserve semibold for navigation identity and concise emphasis.

## Layout

Public header and landing content share side gutters (4.38%), increasing to (6%) below (700px). Desktop navigation is horizontal within a header (52px high); narrow navigation stacks and wraps. The opening layers text over illustrative artwork with an inset purpose index and separate image controls. This composition belongs to the atlas landing surface rather than every page.

Evidence uses three equal columns with vertical rules, simplifies at (1100px), then stacks into ruled rows below (700px). Reading pages have centered content with maximum width (900px), desktop padding (64px 32px 90px) and mobile padding (38px 6% 64px). Reading sections use margins (38px) and top padding (28px).

## Elevation & Depth

Public components have no cast shadows. Paper tones, thin rules, translucent atlas panels and underlying map artwork establish depth.

**The Flat Surfaces Rule.** Use paper tones and thin rules to separate surfaces; public components do not use cast shadows.

## Shapes

Panels and copy controls are square and ruled. Account links and release controls have slight rounding as recorded in frontmatter. Evidence illustrations are circular. Legend swatches are rectangular or linear. Thin dividers carry the editorial structure.

## Components

### Buttons

Release controls use clay fill, pale text and inline SVG. Desktop landing placement may widen them (282px). The action remains disabled while no verified release exists. Copy controls use paper, ink and a thin rule. Atlas controls are square SVG buttons with a pale green hover and muted disabled ink. Public focus outlines use clay (3px) with an offset (5px). Text links thicken their underlines on hover.

### Cards / Containers

The purpose index uses translucent paper, a thin border and ruled links. Rows pair evidence dots with semibold names, descriptions and SVG arrows. Hover adds a pale tonal fill; mobile descriptions move beneath names. Evidence articles are ruled columns rather than floating cards.

### Navigation

The header uses lighter paper, dark text and a bottom rule. Brand text is semibold (25px desktop, 23px mobile); links use (14px desktop, 13px mobile). The account action has a light outline. Hover underlines links. Narrow navigation wraps.

### Evidence illustrations

Pale circles contain inline SVG symbols in matching saturated evidence colors. Circle diameters reduce from (91px) to (64px) at the medium breakpoint. Labels remain readable beside the symbols.

### Atlas artwork and controls

Artwork fills its container, scaling around an origin (65% 50%). Zoom transitions use (0.4s cubic-bezier(0.16, 1, 0.3, 1)); reduced motion removes transitions. Controls change illustration scale and legend visibility. They do not operate scientific data layers. Captions and legend describe illustrative geography.

## Do's and Don'ts

### Do:

- Do pair evidence colors with readable labels.
- Do label illustrative geography and model outputs accurately.
- Do preserve keyboard focus and reduced motion.

### Don't:

- Don't imply the illustration is live monitoring.
- Don't import operator dashboard styling into the public atlas by default.
- Don't invent publication, release or institutional endorsement claims.
