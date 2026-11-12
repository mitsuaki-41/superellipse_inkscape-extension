#!/usr/bin/env python3
import math
import inkex


class Superellipse(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--width", type=float, default=128.0)
        pars.add_argument("--height", type=float, default=128.0)
        pars.add_argument("--exponent", type=float, default=3)
        pars.add_argument("--corner_ratio", type=float, default=0.62)
        pars.add_argument("--precision_level", type=int, default=3)
        pars.add_argument("--unit", type=str, default="px")

    @staticmethod
    def signed_power(value, power):
        if value == 0:
            return 0.0
        return math.copysign(abs(value) ** power, value)

    @staticmethod
    def superellipse_point(t, power):
        return (
            Superellipse.signed_power(math.cos(t), power),
            Superellipse.signed_power(math.sin(t), power),
        )

    @staticmethod
    def superellipse_tangent(t, power):
        eps = 1e-12

        # Start endpoint: t = -pi/2
        if abs(t + math.pi / 2.0) < eps:
            if power < 2.0:
                return 1.0, 0.0
            elif power > 2.0:
                return 0.0, 1.0
            else:
                k = math.sqrt(0.5)
                return k, k

        # End endpoint: t = 0
        if abs(t) < eps:
            if power < 2.0:
                return 0.0, 1.0
            elif power > 2.0:
                return 1.0, 0.0
            else:
                k = math.sqrt(0.5)
                return k, k

        c = math.cos(t)
        s = math.sin(t)

        dx = -s * abs(c) ** (power - 1.0)
        dy = c * abs(s) ** (power - 1.0)

        length = math.hypot(dx, dy)

        if length < 1e-14:
            return 0.0, 0.0

        return dx / length, dy / length

    def fit_handles(self, t0, t1, power):
        """
        Fit one cubic Bezier segment to a superellipse arc.
        Handle lengths are calculated by least squares.
        """
        p0 = self.superellipse_point(t0, power)
        p3 = self.superellipse_point(t1, power)

        tan0 = self.superellipse_tangent(t0, power)
        tan1 = self.superellipse_tangent(t1, power)

        aa = ab = bb = ar = br = 0.0

        for j in range(1, 8):
            u = j / 8.0
            v = 1.0 - u

            q1 = 3.0 * v * v * u
            q2 = 3.0 * v * u * u

            target = self.superellipse_point(
                t0 + (t1 - t0) * u,
                power
            )

            base_x = (
                (v**3 + q1) * p0[0]
                + (q2 + u**3) * p3[0]
            )
            base_y = (
                (v**3 + q1) * p0[1]
                + (q2 + u**3) * p3[1]
            )

            q0x = q1 * tan0[0]
            q0y = q1 * tan0[1]

            q1x = -q2 * tan1[0]
            q1y = -q2 * tan1[1]

            rx = target[0] - base_x
            ry = target[1] - base_y

            aa += q0x * q0x + q0y * q0y
            ab += q0x * q1x + q0y * q1y
            bb += q1x * q1x + q1y * q1y

            ar += q0x * rx + q0y * ry
            br += q1x * rx + q1y * ry

        det = aa * bb - ab * ab

        chord = math.hypot(
            p3[0] - p0[0],
            p3[1] - p0[1]
        )

        h0 = h1 = chord / 3.0

        if abs(det) > 1e-14:
            h0 = (ar * bb - br * ab) / det
            h1 = (br * aa - ar * ab) / det

        limit = max(chord * 2.0, 1e-9)

        return (
            min(max(h0, 0.0), limit),
            min(max(h1, 0.0), limit)
        )

    @staticmethod
    def transform_point(point, cx, cy, radius, angle):
        x, y = point

        c = math.cos(angle)
        s = math.sin(angle)

        return (
            cx + radius * (x * c - y * s),
            cy + radius * (x * s + y * c)
        )

    def effect(self):
        width = float(self.options.width)
        height = float(self.options.height)
        unit = str(self.options.unit)
        exponent = float(self.options.exponent)

        # Convert the entered dimensions to SVG user units (normally px).
        # Coordinates generated below must use the same coordinate system
        # as the document's viewBox.
        try:
            width = self.svg.unittouu(f"{width}{unit}")
            height = self.svg.unittouu(f"{height}{unit}")
        except (ValueError, TypeError) as exc:
            raise inkex.AbortExtension(f"Invalid unit: {unit}") from exc
        corner_ratio = float(self.options.corner_ratio)
        precision_level = int(self.options.precision_level)

        if width <= 0 or height <= 0:
            raise inkex.AbortExtension(
                "Width and height must be greater than zero."
            )

        if exponent <= 0:
            raise inkex.AbortExtension(
                "Exponent must be greater than zero."
            )

        corner_ratio = max(0.0, min(1.0, corner_ratio))

        # SVG viewBox center
        view_box = self.svg.get("viewBox")

        if view_box:
            values = [
                float(v)
                for v in view_box.replace(",", " ").split()
            ]

            if len(values) == 4:
                center_x = values[0] + values[2] / 2.0
                center_y = values[1] + values[3] / 2.0
            else:
                center_x = center_y = 0.0
        else:
            center_x = center_y = 0.0

        left = center_x - width / 2.0
        right = center_x + width / 2.0
        top = center_y - height / 2.0
        bottom = center_y + height / 2.0

        # Corner radius
        radius = ((width + height) / 4.0) * corner_ratio
        radius = min(radius, width / 2.0, height / 2.0)

        commands = []

        if radius <= 1e-9:
            commands = [
                f"M {left:.6f},{top:.6f}",
                f"L {right:.6f},{top:.6f}",
                f"L {right:.6f},{bottom:.6f}",
                f"L {left:.6f},{bottom:.6f}",
                "Z"
            ]

        else:
            power = 2.0 / exponent
            corner_segments = precision_level * 2 - 1

            # Clockwise corner order
            corners = [
                (right - radius, top + radius, 0),
                (right - radius, bottom - radius, 1),
                (left + radius, bottom - radius, 2),
                (left + radius, top + radius, 3),
            ]

            def corner_point(t, corner):
                return self.transform_point(
                    self.superellipse_point(t, power),
                    corner[0],
                    corner[1],
                    radius,
                    corner[2] * math.pi / 2.0
                )

            # Start at the top edge of the top-right corner
            first = corner_point(-math.pi / 2.0, corners[0])

            commands.append(
                f"M {first[0]:.6f},{first[1]:.6f}"
            )

            for i, corner in enumerate(corners):
                angle = corner[2] * math.pi / 2.0

                # Divide each quarter arc into independent Bezier segments
                for j in range(corner_segments):
                    t0 = (
                        -math.pi / 2.0
                        + (math.pi / 2.0) * j / corner_segments
                    )

                    t1 = (
                        -math.pi / 2.0
                        + (math.pi / 2.0) * (j + 1) / corner_segments
                    )

                    p0 = self.superellipse_point(t0, power)
                    p3 = self.superellipse_point(t1, power)

                    tan0 = self.superellipse_tangent(t0, power)
                    tan1 = self.superellipse_tangent(t1, power)

                    h0, h1 = self.fit_handles(t0, t1, power)

                    p1 = (
                        p0[0] + h0 * tan0[0],
                        p0[1] + h0 * tan0[1]
                    )

                    p2 = (
                        p3[0] - h1 * tan1[0],
                        p3[1] - h1 * tan1[1]
                    )

                    cp1 = self.transform_point(
                        p1, corner[0], corner[1], radius, angle
                    )

                    cp2 = self.transform_point(
                        p2, corner[0], corner[1], radius, angle
                    )

                    end = self.transform_point(
                        p3, corner[0], corner[1], radius, angle
                    )

                    commands.append(
                        f"C {cp1[0]:.6f},{cp1[1]:.6f} "
                        f"{cp2[0]:.6f},{cp2[1]:.6f} "
                        f"{end[0]:.6f},{end[1]:.6f}"
                    )

                # Straight edge to the next corner
                next_corner = corners[(i + 1) % 4]

                next_start = corner_point(
                    -math.pi / 2.0,
                    next_corner
                )

                commands.append(
                    f"L {next_start[0]:.6f},{next_start[1]:.6f}"
                )

            commands.append("Z")

        path = inkex.PathElement()
        path.set("d", " ".join(commands))
        path.style = {
            "fill": "#808080",
            "fill-opacity": "0.62",
            "stroke": "none",
        }
        
        # Use the first unused label in the current SVG document.
        existing_labels = {
            element.label
            for element in self.svg.iter()
            if getattr(element, "label", None)
        }
        number = 1
        while f"superellipse{number}" in existing_labels:
            number += 1
        path.label = f"superellipse{number}"

        self.svg.get_current_layer().append(path)


if __name__ == "__main__":
    Superellipse().run()

