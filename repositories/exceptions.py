class TrashFileMissingError(Exception):
    """Raised when the temporary trash file does not exist."""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = 404  # Automatically attaches a 404 code

class FileMoveError(Exception):
    """Raised when moving the file from trash to destination fails."""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = 500  # Automatically attaches a 500 code
