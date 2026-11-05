import unittest
import xml.etree.ElementTree as ET

from wiki_dasboard.extraktion_tools.vertical_svg.generate_svg import build_svg


class TimelineSvgTests(unittest.TestCase):
    def test_eras_keep_background_bands_without_redundant_text(self) -> None:
        data = {
            "title": "Test",
            "subtitle": "Test timeline",
            "min_year": 300,
            "max_year": 2486,
            "pixels_per_year": 0.58,
            "tick_year_step": 100,
            "columns": [
                {
                    "id": "events",
                    "label": "Events",
                    "color": "#2f8a7f",
                    "lanes": 1,
                    "width": 150,
                }
            ],
            "eras": [
                {"label": "Erstes Zeitalter", "start": 300, "end": 1230, "fill": "#f7f1df"},
                {"label": "Zweites Zeitalter", "start": 1231, "end": 2164, "fill": "#efe6d2"},
                {"label": "Drittes Zeitalter", "start": 2165, "end": 2486, "fill": "#e8ddca"},
            ],
            "items": [],
        }

        svg_root = ET.fromstring(build_svg(data))
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        text_content = ["".join(node.itertext()) for node in svg_root.findall("svg:text", namespace)]
        fills = {node.get("fill") for node in svg_root.findall("svg:rect", namespace)}

        self.assertNotIn("Erstes Zeitalter", text_content)
        self.assertNotIn("Zweites Zeitalter", text_content)
        self.assertNotIn("Drittes Zeitalter", text_content)
        self.assertTrue({"#f7f1df", "#efe6d2", "#e8ddca"}.issubset(fills))
        self.assertEqual(len(svg_root.findall("svg:line[@class='era-line']", namespace)), 3)

    def test_point_marker_is_left_aligned_and_label_stays_inside_column(self) -> None:
        column_width = 150
        data = {
            "title": "Test",
            "subtitle": "Test timeline",
            "min_year": 300,
            "max_year": 300,
            "pixels_per_year": 1,
            "tick_year_step": 100,
            "columns": [
                {
                    "id": "events",
                    "label": "Events",
                    "color": "#2f8a7f",
                    "lanes": 1,
                    "width": column_width,
                }
            ],
            "eras": [],
            "items": [
                {
                    "column": "events",
                    "label": "A deliberately long event title",
                    "start": 300,
                    "end": 300,
                    "kind": "point",
                }
            ],
        }

        svg_root = ET.fromstring(build_svg(data))
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        polygon = svg_root.find("svg:polygon", namespace)
        point_label = next(
            text
            for text in svg_root.findall("svg:text", namespace)
            if text.get("class") == "item-label-dark"
        )

        self.assertIsNotNone(polygon)
        assert polygon is not None
        points_attr = polygon.get("points")
        assert points_attr is not None
        marker_x = [
            float(coordinate.split(",")[0])
            for coordinate in points_attr.split()
        ]
        self.assertEqual(min(marker_x), 104)

        label_x_attr = point_label.get("x")
        assert label_x_attr is not None
        label_x = float(label_x_attr)
        column_right = 100 + column_width
        self.assertGreater(label_x, max(marker_x))
        self.assertLess(label_x, column_right - 8)
        max_chars = int((column_right - 8 - label_x) / 6)
        lines = [span.text or "" for span in point_label.findall("svg:tspan", namespace)]
        self.assertGreater(len(lines), 1)
        self.assertLessEqual(max(map(len, lines)), max_chars)

    def test_dense_point_labels_do_not_overlap_or_overflow_svg_bottom(self) -> None:
        data = {
            "title": "Test",
            "subtitle": "Test timeline",
            "min_year": 300,
            "max_year": 360,
            "pixels_per_year": 1,
            "tick_year_step": 100,
            "columns": [
                {
                    "id": "events",
                    "label": "Events",
                    "color": "#2f8a7f",
                    "lanes": 1,
                    "width": 250,
                }
            ],
            "eras": [],
            "items": [
                {
                    "column": "events",
                    "label": f"Long event title with enough words to wrap {index}",
                    "start": year,
                    "end": year,
                    "kind": "point",
                }
                for index, year in enumerate((359, 359, 360, 360))
            ],
        }

        svg_root = ET.fromstring(build_svg(data))
        point_labels = [
            text
            for text in svg_root.findall("svg:text", {"svg": "http://www.w3.org/2000/svg"})
            if text.get("class") in {
                "item-label-dark",
                "item-label-dark-small",
                "item-label-dark-tiny",
            }
        ]
        boxes = []
        font_sizes = {
            "item-label-dark": 10,
            "item-label-dark-small": 8.5,
            "item-label-dark-tiny": 7,
        }
        for label in point_labels:
            label_y = label.get("y")
            class_name = label.get("class")
            assert label_y is not None
            assert class_name in font_sizes
            baselines = [float(label_y)]
            for span in label.findall(
                "svg:tspan", {"svg": "http://www.w3.org/2000/svg"}
            )[1:]:
                baselines.append(baselines[-1] + float(span.get("dy", "0")))
            font_size = font_sizes[class_name]
            boxes.append((baselines[0] - font_size, baselines[-1] + font_size * 0.3))

        self.assertEqual(len(boxes), 4)
        boxes.sort()
        for previous, current in zip(boxes, boxes[1:]):
            self.assertGreaterEqual(current[0], previous[1])
        svg_height = svg_root.get("height")
        assert svg_height is not None
        self.assertLessEqual(max(box[1] for box in boxes), float(svg_height) - 8)


if __name__ == "__main__":
    unittest.main()