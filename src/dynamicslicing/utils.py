from typing import List, Union, Optional
import libcst as cst
from libcst._flatten_sentinel import FlattenSentinel
from libcst._nodes.statement import BaseStatement, If
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

    def leave_If(self, original_node: If, updated_node: If) -> BaseStatement | FlattenSentinel[BaseStatement] | cst.RemovalSentinel:
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
    def __init__(self, lines_to_keep: set) -> None:
        super().__init__()
        self.lines_to_keep = lines_to_keep
    
    def on_visit(self, node: cst.CSTNode) -> bool:
        location = self.get_metadata(PositionProvider, node)
        if int(location.start.line) in self.lines_to_keep:
            return True
        return False
    
    def on_leave(
        self, original_node: cst.CSTNodeT, updated_node: cst.CSTNodeT
    ) -> Union[cst.CSTNodeT, cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            # print(f"Removing line {location.start.line}")
            # try:
            # create_empty_module()
            return cst.RemoveFromParent()
            # except Exception as e:
                # create_empty_module()
                # print("error")
        return updated_node

def negate_odd_ifs(code: str) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = OddIfNegation()
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def remove_lines(code: str, lines_to_keep: List[int]) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = RemoveLines(lines_to_keep)
    new_syntax_tree = wrapper.visit(code_modifier)
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

lines_to_keep = {1, 2, 4, 5, 9}
x = remove_lines(original_code, lines_to_keep)
print(x)