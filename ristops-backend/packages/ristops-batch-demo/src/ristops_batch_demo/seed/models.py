from pydantic import BaseModel, Field

from ristops_lib_core.schema.authz import ResourceType


class DemoAcl(BaseModel):
    """ Used to assign roles to demo users"""
    role_id: str
    resource_id: str
    resource_type: ResourceType


class DemoUser(BaseModel):
    username: str = Field()
    email: str = Field()
    display_name: str | None = Field(None)
    password: str | None = Field("password")

    acl: list[DemoAcl] | None = Field(None)


class DemoData(BaseModel):
    users: list[DemoUser] = Field()
