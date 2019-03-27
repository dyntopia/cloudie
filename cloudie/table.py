import shutil
from typing import Any, List

import texttable


def show(columns: List[List[str]], rows: List[object]) -> None:
    """
    Show a table with the given columns for each row.

    :param columns: The first string in each sub-list is used as the
        header for that column.  The proceeding string(s) specifies the
        attribute name(s) for that column in `rows`.  The first found
        attribute is used as the column value.
    :param rows: A list of objects to retrieve the column values from.
    """
    size = shutil.get_terminal_size()
    table = texttable.Texttable(max_width=size.columns)
    table.set_deco(table.VLINES | table.HEADER)

    table.header([column[0] for column in columns])
    table.set_cols_dtype(["t" for _ in range(len(columns))])

    table.add_rows([[[
        next((
            isinstance(v, list) and ", ".join(str(elm) for elm in v)
            or v for v in (_get_value(row, name) for name in column[1:]) if v
        ), "")
    ][0] for column in columns] for row in rows], False)

    print(table.draw())


def _get_value(obj: object, name: str, default: Any = None) -> Any:
    """
    Recursively retrieve a value from an object.

    :param obj: An object to retrieve the value from.
    :param name: The name of the value.
    :param default: Default value if `name` isn't found.
    :returns: The value for `name` or `default`.
    """
    for elem in name.split("."):
        if isinstance(obj, dict):
            obj = obj.get(elem, default)
        else:
            obj = getattr(obj, elem, default)

    return obj or default
