class ValidationError:
    def __init__(self, message):
        self.message = message

    def __bool__(self):
        return False
