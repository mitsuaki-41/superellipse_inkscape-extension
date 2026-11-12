# Superellipse (Inkscape Extension)

An Inkscape extension for generating superellipse shapes, including squircles, using cubic Bézier curves and straight lines.

## Features

- Generate superellipse shapes with adjustable dimensions.
- Control the shape using an exponent parameter.
- Adjust corners radius.
- Set curve approximation precision.
- The extension creates a closed SVG path in the current layer, centered on the document's viewBox.
- The generated path can be edited using Inkscape's Node tool.

## Parameters

| Parameter | Description | Range | Default |
|---|---|---|---|
| Unit | Measurement unit | px, mm, cm, in, pt, pc | px |
| Width | Shape width | 1–2048 | 128 |
| Height | Shape height | 1–2048 | 128 |
| Exponent | Controls corner curvature | 1–18 | 3 |
| Corner Ratio | Controls corner radius | 0–1 | 0.62 |
| Precision Level | Bézier approximation precision | 1–6 | 3 |

an exponent of 2 produces circular corners, while a higher exponent produces squarer corners.

## Installation

1. Download or clone this repository.
2. Place both files in your Inkscape extensions directory.
Linux: `~/.config/inkscape/extensions`
3. Restart Inkscape.

The extension is available under `Extensions` → `Render` → `Superellipse`.

##License
MIT
