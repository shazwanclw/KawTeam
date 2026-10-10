from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NewBrief(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    title: str = Field(min_length=1, max_length=100)
    goal: str = Field(min_length=1, max_length=2000)
    quantity: int | None = Field(default=None, gt=0, strict=True)
    budget_sen: int | None = Field(default=None, alias="budgetSen", gt=0, strict=True)
    target_sen: int | None = Field(default=None, alias="targetSen", gt=0, strict=True)
    deadline: date | None = None
    location: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def check_boundaries(self) -> Self:
        if self.target_sen is not None and self.budget_sen is not None and self.target_sen > self.budget_sen:
            raise ValueError("Target must be within the hard budget")
        if not all(value.strip() for value in (self.title, self.goal)) or (self.location is not None and not self.location.strip()):
            raise ValueError("Brief fields must not be blank")
        return self


class VendorChoice(BaseModel):
    """Human API command, deliberately absent from the agent's MCP tools."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    case_id: str = Field(alias="caseId", min_length=1)
    vendor_id: str = Field(alias="vendorId", min_length=1)
    actor: Literal["organiser"]
