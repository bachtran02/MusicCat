import typing
from typing_extensions import Self

from hikari.api.special_endpoints import AutocompleteChoiceBuilder

class AutocompleteChoice(AutocompleteChoiceBuilder):

    def __init__(self, title, uri) -> None:
        self.name = title
        self.value = uri

    def name(self) -> str:
        return self.name

    def value(self) -> typing.Union[int, str, float]:
        return self.value

    def set_name(self, name: str, /) -> Self:
        self.name = name

    def set_value(self, value: typing.Union[int, float, str], /) -> Self:
        self.value = value
    
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {'name': self.name, 'value': self.value}

