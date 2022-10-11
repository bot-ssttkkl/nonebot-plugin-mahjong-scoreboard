class BadRequestError(Exception):
    def __init__(self, message=None):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


class ApiError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__()
        self.code = code
        self.message = message
