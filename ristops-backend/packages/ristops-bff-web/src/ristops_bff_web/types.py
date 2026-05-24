from typing import Annotated

import strawberry

EntityId = Annotated[
    strawberry.ID,
    strawberry.argument(description="Entity identifier.", name="id")
]
