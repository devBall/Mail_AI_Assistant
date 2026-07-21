from uuid import UUID


class EmailNotFoundError(Exception):
    def __init__(self, email_id: UUID) -> None:
        super().__init__(f"Email with id '{email_id}' was not found.")
        self.email_id = email_id