from unittest import TestCase
from unittest.mock import patch

from cloudie import table

from .helpers import TexttableMock


class Obj:
    string1 = "abcd"
    string2 = "xyz"
    lst = ["aa", 123]
    large_int = 1000000000
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
    def test_values(self) -> None:
        t = TexttableMock()
        with patch("texttable.Texttable") as mock:
            mock.return_value = t
            table.show([
                ["String1", "no_string", "string1"],
                ["String2", "string2", "string1"],
                ["Empty", "does", "not", "exist"],
                ["List1", "lst", "none"],
                ["List2", "dct.second.list"],
                ["Int", "dct.third.int"],
                ["Large int", "large_int"],
                ["string1", "dct.second.list", "xyz"],
            ], [Obj(), Obj()])

            headers = [
                "String1",
                "String2",
                "Empty",
                "List1",
                "List2",
                "Int",
                "Large int",
                "string1",
            ]
            self.assertEqual(t.headers, headers)

            rows = [
                ["abcd", "xyz", "", "aa, 123", "x", "321", "1000000000", "x"],
                ["abcd", "xyz", "", "aa, 123", "x", "321", "1000000000", "x"],
            ]
            self.assertEqual(t.rows, rows)


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
