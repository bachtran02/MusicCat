import typing

from hikari.api.special_endpoints import AutocompleteChoiceBuilder

class AutocompleteChoice(AutocompleteChoiceBuilder):

    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value

    def name(self) -> str:
        return self.name

    def value(self) -> typing.Union[int, str, float]:
        return self.value

    def set_name(self, name: str, /):
        self.name = name

    def set_value(self, value: typing.Union[int, float, str], /):
        self.value = value
    
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {'name': self.name, 'value': self.value}

