from unittest import TestCase
from unittest.mock import patch

from cloudie import table


class Obj:
    string1 = "abcd"
    string2 = "xyz"
    lst = ["aa", 123]
    dct = {
        "first": ["aaa", "bbb"],
        "second": {
            "list": ["x"],
        },
        "third": {
            "int": 321
        }
    }


class TestTable(TestCase):
    @staticmethod
    def test_values() -> None:
        with patch("texttable.Texttable.header") as header:
            with patch("texttable.Texttable.add_rows") as add_rows:
                table.show([
                    ["String1", "no_string", "string1"],
                    ["String2", "string2", "string1"],
                    ["Empty", "does", "not", "exist"],
                    ["List1", "lst", "none"],
                    ["List2", "dct.second.list"],
                    ["Int", "dct.third.int"],
                    ["string1", "dct.second.list", "xyz"],
                ], [Obj(), Obj()])

                header.assert_called_with([
                    "String1",
                    "String2",
                    "Empty",
                    "List1",
                    "List2",
                    "Int",
                    "string1",
                ])

                add_rows.assert_called_with([
                    ["abcd", "xyz", "", "aa, 123", "x", 321, "x"],
                    ["abcd", "xyz", "", "aa, 123", "x", 321, "x"],
                ], False)


class TestGetValue(TestCase):
    def test_values(self) -> None:
        # pylint: disable=protected-access
        self.assertEqual(table._get_value(Obj, "string1"), "abcd")
        self.assertEqual(table._get_value(Obj, "string2"), "xyz")
        self.assertEqual(table._get_value(Obj, "lst"), ["aa", 123])
        self.assertEqual(table._get_value(Obj, "dct.first"), ["aaa", "bbb"])
        self.assertEqual(table._get_value(Obj, "dct.second"), {"list": ["x"]})
        self.assertEqual(table._get_value(Obj, "dct.second.list"), ["x"])
        self.assertEqual(table._get_value(Obj, "dct.third"), {"int": 321})
        self.assertEqual(table._get_value(Obj, "dct.third.int"), 321)
        # pylint: enable=protected-access
