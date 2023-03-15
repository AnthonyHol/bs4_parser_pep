class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""

    pass


class UnexpectedStatusException(Exception):
    """Вызывается, когда был возвращен непредвиденный статус."""

    pass
