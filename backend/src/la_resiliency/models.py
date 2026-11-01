import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
LangCode = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]
Url = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^https?://[^\s]+$")]
PhoneNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^(?:\d11|(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4})$",
    ),
]
Audience = Literal["everyone", "church_members", "seniors", "families", "students"]
Cost = Literal["", "free", "paid", "varies"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Phone(Strict):
    number: PhoneNumber
    label: Text = ""
    lang: LangCode | None = None

    @property
    def tel(self) -> str:
        digits = re.sub(r"\D", "", self.number)
        return {3: digits}.get(len(digits), f"+1{digits[-10:]}")


class Resource(Strict):
    id: Slug
    categories: list[Slug] = Field(min_length=1)
    name: Text = Field(min_length=1)
    url: Url | None = None
    phones: list[Phone] = []
    description: Text = Field(min_length=1)
    who_its_for: Text = ""
    how_to_get_it: Text = ""
    tip: Text = ""
    audience: Audience = "everyone"
    status_ok: bool = False
    cost: Cost = ""
    languages: list[LangCode] = []
    multilingual: bool = False
    urgent: bool = False
    volatile: bool = False
    last_verified: date
    active: bool = True


class Category(Strict):
    id: Slug
    icon: str
    label: Text
    blurb: Text
    urgent: bool = False
