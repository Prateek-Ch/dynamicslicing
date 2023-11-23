from typing import List, Union
import libcst as cst
from libcst._flatten_sentinel import FlattenSentinel
from libcst._nodes.statement import BaseStatement, If
from libcst._removal_sentinel import RemovalSentinel, RemoveFromParent
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
)
import libcst.matchers as m


class OddIfNegation(m.MatcherDecoratableTransformer):
    """
    Negate the test of every if statement on an odd line.
    """
    METADATA_DEPENDENCIES = (
        ParentNodeProvider,
        PositionProvider,
    )

    def leave_If(self, original_node: If, updated_node: If) -> BaseStatement | FlattenSentinel[BaseStatement] | RemovalSentinel:
        location = self.get_metadata(PositionProvider, original_node)
        if location.start.line % 2 == 0:
            return updated_node
        negated_test = cst.UnaryOperation(
            operator=cst.Not(),
            expression=updated_node.test,
        )
        return updated_node.with_changes(
            test=negated_test,
        )

class RemoveLines(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    )
    def __init__(self, lines_to_remove: set) -> None:
        super().__init__()
        self.lines_to_remove = lines_to_remove
    
    def on_leave(
        self, original_node: cst.CSTNode, updated_node: cst.CSTNode
    ) -> Union[cst.CSTNodeT, RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) in self.lines_to_remove:
            print(f"Removing line {location.start.line}")
            return RemoveFromParent()
        return updated_node

def negate_odd_ifs(code: str) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = OddIfNegation()
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def remove_lines(code: str, lines_to_remove: List[int]) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = RemoveLines(lines_to_remove)
    new_syntax_tree = wrapper.visit(code_modifier)
    print(new_syntax_tree.code)
    return new_syntax_tree.code


# Example usage:
original_code = """def slice_me():
    x = 5
    print("Hello World")
    if x < 10:
        x += 5
    y = 0
    return y

slice_me()
"""

lines_to_remove = {1, 2, 4, 5, 9}

remove_lines(original_code, lines_to_remove)