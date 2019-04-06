class InvalidContentType(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

class EmptyChangeID(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

class RepeatedID(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors

