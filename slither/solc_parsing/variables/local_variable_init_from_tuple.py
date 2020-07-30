from slither.core.variables.local_variable_init_from_tuple import LocalVariableInitFromTuple
from .variable_declaration import VariableDeclarationSolc
from ..types.types import VariableDeclarationStatement


class LocalVariableInitFromTupleSolc(VariableDeclarationSolc):
    def __init__(self, variable: LocalVariableInitFromTuple, variable_data: VariableDeclarationStatement, index: int):
        super(LocalVariableInitFromTupleSolc, self).__init__(variable, variable_data)
        variable.tuple_index = index

    @property
    def underlying_variable(self) -> LocalVariableInitFromTuple:
        # Todo: Not sure how to overcome this with mypy
        assert isinstance(self._variable, LocalVariableInitFromTuple)
        return self._variable
