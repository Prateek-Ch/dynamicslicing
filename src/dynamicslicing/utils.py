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
            return cst.RemoveFromParent()
        return updated_node
    
    def leave_If(
       self, original_node: "If", updated_node: "If"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            updated_node = cst.RemoveFromParent()
        return updated_node


class SlicingCriterionLocation(cst.CSTTransformer):
    """
        Returns the slicing criterion location
    """
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    ) 
    
    def __init__(self):
        super().__init__()
        self.slicing_criterion_location = None
       
    def leave_Comment(
        self, original_node: "Comment", updated_node: "Comment"
    ) -> "Comment":
        location = self.get_metadata(PositionProvider, original_node)
        if "# slicing criterion" in original_node.value:
            self.slicing_criterion_location = int(location.start.line)
        return original_node
    
    def get_slicing_criterion_location(self):
        return self.slicing_criterion_location
    
class SlicingCriterion(cst.CSTTransformer):
    """
        Returns the slicing criterion
    """
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    ) 
    def __init__(self, slicing_criterion_location: int) -> None:
        super().__init__()
        self.slicing_criterion_location = slicing_criterion_location
        self.slicing_criterion = set()
    
    def on_leave(
        self, original_node: cst.CSTNodeT, updated_node: cst.CSTNodeT
    ) -> Union[cst.CSTNodeT, cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) == self.slicing_criterion_location:
            if isinstance(updated_node, cst.SimpleStatementLine):
                if len(updated_node.body) > 0 and isinstance(updated_node.body[0], cst.Return):
                    return_expr = updated_node.body[0].value
                    if isinstance(return_expr, cst.Name):
                        self.slicing_criterion.add(return_expr.value)
                elif len(updated_node.body) > 0 and isinstance(updated_node.body[0], cst.Assign):
                    assignment_value = updated_node.body[0].value
                    self.collect_variables(assignment_value)
        return updated_node
    
    def get_slicing_criterion(self):
        return self.slicing_criterion

    def collect_variables(self, node):
        if isinstance(node, cst.Name):
            self.slicing_criterion.add(node.value)
        elif isinstance(node, cst.BinaryOperation):
            self.collect_variables(node.left)
            self.collect_variables(node.right)

def negate_odd_ifs(code: str) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = OddIfNegation()
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def remove_lines(code: str, lines_to_keep: []) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    code_modifier = RemoveLines(lines_to_keep)
    new_syntax_tree = wrapper.visit(code_modifier)
    return new_syntax_tree.code

def slicing_criterion(code: str) -> str:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    
    slicing_criterion_location = SlicingCriterionLocation()
    scl_ayntax_tree = wrapper.visit(slicing_criterion_location)
    
    slicing_criterion = SlicingCriterion(slicing_criterion_location.get_slicing_criterion_location())
    sc_synyax_tree = wrapper.visit(slicing_criterion)
    return slicing_criterion.get_slicing_criterion()

# original_code = """def slice_me():
#     x = 5
#     print("Hello World")  
#     if x < 10:
#         x += 5
#     y = 0
#     return y # slicing criterion

# slice_me()
# """

original_code = """def slice_me():
    x = 10
    y = 20
    z = x + y # slicing criterion

slice_me()
"""

# lines_to_keep = [1, 2, 4, 5, 9]
# x = remove_lines(original_code, lines_to_keep)
# print(x)

y = slicing_criterion(original_code)
print(y)