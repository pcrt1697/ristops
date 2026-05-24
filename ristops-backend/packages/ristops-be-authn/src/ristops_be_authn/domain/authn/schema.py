from typing import Literal

from pydantic import BaseModel, Field


class JWK(BaseModel):
    kty: Literal["EC", "RSA", "oct"] = Field(
        description=(
            "Key type. Identifies the cryptographic algorithm family. "
            "EC for elliptic curve, RSA, or oct for symmetric keys."
        ),
    )
    use: Literal["sig", "enc"] | None = Field(
        default=None,
        description="Intended use of the key. 'sig' for signature verification, 'enc' for encryption.",
    )
    alg: str | None = Field(
        default=None,
        description="Algorithm intended for use with this key, e.g. 'ES256', 'RS256'.",
    )
    kid: str | None = Field(
        default=None,
        description="Key ID. Used to match a specific key in a JWKS when multiple keys are present.",
    )
    crv: Literal["P-256", "P-384", "P-521"] | None = Field(
        default=None,
        description="EC curve name. Required for EC keys. P-256 corresponds to ES256, P-384 to ES384, P-521 to ES512.",
    )
    x: str | None = Field(
        default=None,
        description="Base64url-encoded x coordinate of the EC public key point.",
    )
    y: str | None = Field(
        default=None,
        description="Base64url-encoded y coordinate of the EC public key point.",
    )


class JWKResponse(BaseModel):
    keys: list[JWK] = Field(
        description=(
            "Array of JWK public keys. "
            "Clients should use the 'kid' field to select the appropriate key for verification."
        ),
    )
