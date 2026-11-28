"""The route cipher: scramble whole words by walking a grid.

Write the message into a grid, left to right and top to bottom, like
filling pigeonholes. Then read it back out *down and up the columns*,
in an order only the sender and receiver know. The words are all real,
which telegraph clerks liked (they garble far fewer real words than
random letters), but they come out in the wrong order.

The route is written as a **key**: one number per column, counting from
1 like people do. A positive number means "read that column top to
bottom", a negative one "bottom to top". ``-1 2 -3`` means: up the
first column, down the second, up the third.

Cells are numbered across the rows, the way the message was written::

    0  1  2        a 3-column, 2-row grid
    3  4  5
"""

Words = list[str]  # a message, one word per item
Key = list[int]  # a route: one signed column number per column


class TelegramProblem(ValueError):
    """Something about the telegram's settings doesn't add up.

    Raising our own kind of error, with a message written for a person,
    lets the command line print it nicely and the tests check for it,
    without catching unrelated mistakes by accident.
    """


class KeyProblem(TelegramProblem):
    """The key (the route through the columns) can't be used."""


class GridProblem(TelegramProblem):
    """The grid's columns and rows don't fit the message."""


def factors(count: int) -> list[int]:
    """The column (or row) counts a ``count``-word grid could have.

    1 and ``count`` are left out: a grid one column wide or one row tall
    reads straight back as the original message, so it hides nothing.
    """
    return [size for size in range(2, count) if count % size == 0]


def check_grid(count: int, cols: int, rows: int) -> None:
    """Raise ``GridProblem`` unless ``cols`` × ``rows`` holds every word."""
    if cols < 1 or rows < 1:
        raise GridProblem("A grid needs at least one column and one row.")
    if cols * rows != count:
        fit = ", ".join(str(size) for size in factors(count)) or "none"
        raise GridProblem(
            f"{cols} columns × {rows} rows is {cols * rows} pigeonholes, "
            f"but the telegram has {count} words. "
            f"Column counts that fit: {fit}."
        )


def check_key(key: list[int], cols: int) -> list[int]:
    """Return the key unchanged if it's usable, else raise ``KeyProblem``.

    Each check matches a slip a person might really make, and says how
    to fix it.
    """
    if 0 in key:
        raise KeyProblem("Columns count from 1, so the key can't use 0.")
    for number in key:
        if abs(number) > cols:
            column = abs(number)
            message = f"Only {cols} columns here, so no column {column}."
            raise KeyProblem(message)
    if len(key) != cols:
        given = len(key)
        message = f"The key needs {cols} numbers, one per column, not {given}."
        raise KeyProblem(message)
    seen = [abs(number) for number in key]
    for column in seen:
        if seen.count(column) > 1:
            message = f"Column {column} is in the key twice. Use each once."
            raise KeyProblem(message)
    return key


def parse_key(text: str, cols: int) -> list[int]:
    """Turn typed text like ``"-1 2 -3"`` or ``"-1, 2, -3"`` into a key."""
    key = []
    for token in text.replace(",", " ").split():
        try:
            key.append(int(token))
        except ValueError:
            message = f'"{token}" isn\'t a column number, like -1 2 -3.'
            raise KeyProblem(message) from None
    return check_key(key, cols)


def route_order(cols: int, rows: int, key: list[int]) -> list[int]:
    """The cell numbers in the order the route visits them.

    For each column in the key, list its cells top to bottom (or bottom
    to top for a negative number). The web page uses this list to draw
    the route through the pigeonholes.
    """
    check_key(key, cols)
    order = []
    for number in key:
        column = abs(number) - 1  # people count from 1, Python from 0
        down = range(rows) if number > 0 else range(rows - 1, -1, -1)
        order.extend(row * cols + column for row in down)
    return order


def encrypt(words: Words, cols: int, rows: int, key: Key) -> Words:
    """Read the words out of the grid along the route."""
    check_grid(len(words), cols, rows)
    return [words[cell] for cell in route_order(cols, rows, key)]


def build_matrix(cipher: Words, rows: int, key: Key) -> list[Words]:
    """Put the ciphertext back into its columns, ready to read off.

    The ciphertext is the columns laid end to end, ``rows`` words each,
    in the order the key visited them. Slice out each run of words, and
    store every column the same way round, *bottom word first*, in its
    own slot. A column read upward already is bottom first; one read
    downward is flipped with the ``[::-1]`` slice.

    Bottom first, so that ``list.pop()`` (which takes the *last* item)
    hands back the top word.
    """
    matrix: list[list[str]] = [[] for _ in key]
    for position, number in enumerate(key):
        run = cipher[position * rows : (position + 1) * rows]
        matrix[abs(number) - 1] = run if number < 0 else run[::-1]
    return matrix


def decrypt_matrix(matrix: list[list[str]]) -> list[str]:
    """Read the matrix row by row, popping the top word off each column.

    Each pass across the columns takes one word from every column: the
    top row on the first pass, the next row on the second, and so on.
    ``pop`` empties the matrix as it goes, which is fine: we're done
    with it.
    """
    rows = len(matrix[0]) if matrix else 0
    words = []
    for _ in range(rows):
        for column in matrix:
            words.append(column.pop())
    return words


def decrypt(cipher: Words, cols: int, rows: int, key: Key) -> Words:
    """Undo the route cipher: back into the grid, then read across the rows."""
    check_grid(len(cipher), cols, rows)
    check_key(key, cols)
    return decrypt_matrix(build_matrix(cipher, rows, key))
