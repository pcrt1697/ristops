from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

ObjectUUID = Annotated[
    UUID,
    Field(
        description="Resource identifier.",
    )
]

CreatedAt = Annotated[
    datetime,
    Field(
        description="Date and time when the object was created.",
    )
]

UpdatedAt = Annotated[
    datetime,
    Field(
        description="Date and time when the object was updated.",
    )
]

DeletedAt = Annotated[
    datetime | None,
    Field(
        default=None,
        description="Date and time when the object was deleted; null while active.",
    )
]
