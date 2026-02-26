import unittest

from nin import parse_input


class ParseInputTests(unittest.TestCase):
    def test_title_and_body_without_space(self) -> None:
        self.assertEqual(parse_input("title,body"), ("title", "body"))

    def test_title_and_body_with_space(self) -> None:
        self.assertEqual(parse_input("title, body"), ("title", "body"))

    def test_title_only(self) -> None:
        self.assertEqual(parse_input("title"), ("title", ""))

    def test_title_with_trailing_comma(self) -> None:
        self.assertEqual(parse_input("title,"), ("title", ""))

    def test_body_keeps_additional_commas(self) -> None:
        self.assertEqual(parse_input("title, body, more"), ("title", "body, more"))

    def test_empty_title_raises_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_input(", body")
        self.assertIn("タイトルが空です。", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
