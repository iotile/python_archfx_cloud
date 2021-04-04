from typedargs.exceptions import KeyValueException as IOTileException


class DataError(IOTileException):
    """The method relied on data pass in by the user and the data was invalid.
    This could be because a file was the wrong type or because a data provider
    returned an unexpected result.  The parameters passed with this exception
    provide more detail on what occurred and where.
    """

    pass
