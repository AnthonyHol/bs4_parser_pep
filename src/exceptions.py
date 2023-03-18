class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""

    pass


class UnexpectedStatusException(Exception):
    """Вызывается, когда был возвращен непредвиденный статус."""

    pass


class TagNotFoundException(Exception):
    """Вызывается, когда тег не был найден."""

    pass
