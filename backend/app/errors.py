class AppError(Exception):
    """error aturan bisnis yang pesannya aman ditampilkan ke pengguna"""

    status_code = 400

    def __init__(self, pesan: str, status_code: int | None = None):
        super().__init__(pesan)
        self.pesan = pesan
        if status_code is not None:
            self.status_code = status_code

class NotFound(AppError):
    status_code = 404

class Conflict(AppError):
    status_code = 409
