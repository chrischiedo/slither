from typing import Dict

from .variable_declaration import VariableDeclarationSolc
from slither.core.variables.event_variable import EventVariable
from ..types.types import VariableDeclaration


class EventVariableSolc(VariableDeclarationSolc[EventVariable]):
    def __init__(self, variable: EventVariable, variable_data: VariableDeclaration):
        super(EventVariableSolc, self).__init__(variable, variable_data)

    def _analyze_variable_attributes(self, attributes: VariableDeclaration):
        """
        Analyze event variable attributes
        :param attributes: The event variable attributes to parse.
        :return: None
        """

        # Check for the indexed attribute
        if "indexed" in attributes:
            self.underlying_variable.indexed = attributes["indexed"]

        super(EventVariableSolc, self)._analyze_variable_attributes(attributes)
