"""Financial value types that are safe at the AI structured-output boundary."""

from decimal import Decimal
from typing import Annotated

from pydantic import WithJsonSchema


# Pydantic normally publishes Decimal as number-or-string with a lookaround
# regex. OpenAI Structured Outputs does not support that regex feature. The
# provider receives a plain JSON number contract while Pydantic still converts
# and validates the value as Decimal inside Moneytiqx.
AIMoney = Annotated[
    Decimal,
    WithJsonSchema({"type": "number"}),
]
