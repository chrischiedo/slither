from slither.core.variables.local_variable import LocalVariable
from .variable_declaration import VariableDeclarationSolc
from ..types.types import VariableDeclarationStatement, VariableDeclaration


class LocalVariableSolc(VariableDeclarationSolc[LocalVariable]):
    def __init__(self, variable: LocalVariable, variable_data: VariableDeclarationStatement):
        super(LocalVariableSolc, self).__init__(variable, variable_data)

    def _analyze_variable_attributes(self, attributes: VariableDeclaration):
        """'
            Variable Location
            Can be storage/memory or default
        """
        # TODO
        # if "storageLocation" in attributes:
        #     location = attributes["storageLocation"]
        #     self.underlying_variable.set_location(location)
        # else:
        #     if "memory" in attributes["type"]:
        #         self.underlying_variable.set_location("memory")
        #     elif "storage" in attributes["type"]:
        #         self.underlying_variable.set_location("storage")
        #     else:
        #         self.underlying_variable.set_location("default")

        super()._analyze_variable_attributes(attributes)
