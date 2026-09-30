"""Pure Windows directory-component validation; text is returned verbatim."""

_INVALID = set('<>:"/\\|?*')
_RESERVED = {"CON", "PRN", "AUX", "NUL"}
_RESERVED.update(f"{prefix}{suffix}" for prefix in ("COM", "LPT")
                 for suffix in "123456789¹²³")


class InvalidRootNameError(ValueError):
    """The proposed child is not one valid Windows directory component."""


def validate_child_name(name: str) -> str:
    if (not isinstance(name, str) or not name or name in {".", ".."}
            or name[-1] in {".", " "}
            or any(character in _INVALID or ord(character) < 32 for character in name)
            or len(name.encode("utf-16-le")) // 2 > 255
            or name.split(".", 1)[0].upper() in _RESERVED):
        raise InvalidRootNameError("Choose one valid Windows directory name.")
    return name
