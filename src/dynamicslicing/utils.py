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
    
    def leave_SimpleStatementLine(
        self, original_node: "SimpleStatementLine", updated_node: "SimpleStatementLine"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            updated_node = cst.RemoveFromParent()
        return updated_node
    
    def leave_If(
       self, original_node: "If", updated_node: "If"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            updated_node = cst.RemoveFromParent()
        return updated_node
    
    def leave_Else(self, original_node: "Else", updated_node: "Else") -> "Else":
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            updated_node = cst.RemoveFromParent()
        return updated_node
    
    def leave_For(
        self, original_node: "For", updated_node: "For"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            updated_node = cst.RemoveFromParent()
        return updated_node

    def leave_While(
        self, original_node: "While", updated_node: "While"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        if int(location.start.line) not in self.lines_to_keep:
            updated_node = cst.RemoveFromParent()
        return updated_node
    
    def leave_Comment(
        self, original_node: "Comment", updated_node: "Comment"
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
            if isinstance(updated_node, cst.Name):
                self.slicing_criterion.add(updated_node.value)
            if isinstance(updated_node, cst.SimpleStatementLine):
                if len(updated_node.body) > 0 and isinstance(updated_node.body[0], cst.Return):
                    return_expr = updated_node.body[0].value
                    if isinstance(return_expr, cst.Name):
                        self.slicing_criterion.add(return_expr.value)
                    if isinstance(return_expr, cst.Attribute):
                        object_value = return_expr.value.value
                        object_attr = return_expr.attr.value
                        self.slicing_criterion.add(object_value + "." + object_attr)
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
    
class GetClassInformation(cst.CSTTransformer):
    """ 
    Returns the class information
    """
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    ) 
    def __init__(self) -> None:
        super().__init__()
        self.class_location = []
        
    def visit_ClassDef(self, node: "ClassDef") -> None:
        location = self.get_metadata(PositionProvider, node)
        self.class_location.extend(range(int(location.start.line),int(location.end.line)+1))
        
    def class_info(self):
        return self.class_location

class GetIfInformation(cst.CSTTransformer):
    """
    Returns the if information
    """
    
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    )
    
    def __init__(self, slicing_criterion: set) -> None:
        super().__init__()
        self.if_information = []
        self.slicing_criterion = slicing_criterion
        self.remove_information = []
        self.else_required = False
        self.if_required = False
        
    def leave_If(
        self, original_node: "If", updated_node: "If"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        # In case else is required add the Comparision vars to list of slicing_criterions
        if self.else_required:
            if isinstance(original_node.test, cst.Comparison) and original_node.test.left.value not in self.slicing_criterion:
                self.slicing_criterion.add(original_node.test.left.value)
            if isinstance(original_node.test, cst.BooleanOperation):
                if original_node.test.left.left.value not in self.slicing_criterion:
                    self.slicing_criterion.add(original_node.test.left.left.value)
                if original_node.test.right.left.value not in self.slicing_criterion:
                    self.slicing_criterion.add(original_node.test.right.left.value)
        
        # Perform check for If condition and add vals to slicing_criterion as needed
        if isinstance(original_node.body.body[0], cst.SimpleStatementLine):
            for i in range(len(original_node.body.body)):
                body  = original_node.body.body[i].body[0]
                value = ''
                if isinstance(body, cst.Expr) and hasattr(body.value.func, 'attr') and body.value.func.attr.value == 'append':
                    value = body.value.func.value.value
                if isinstance(body, cst.AugAssign):
                    if isinstance(body.target.value, cst.Name):
                        value = body.target.value.value
                    else: value = body.target.value
                if isinstance(body, cst.Assign) and isinstance(body.targets[0], cst.AssignTarget):
                    value = body.targets[0].target.value.value  #for cases like p.name = something, we set value to p
                    
                if value in self.slicing_criterion:
                    self.if_required = True
                    self.if_information.extend(range(int(location.start.line), int(location.end.line)+1))
                    if isinstance(original_node.test, cst.Comparison) and original_node.test.left.value not in self.slicing_criterion:
                        if hasattr(original_node.test.left, "attr"):
                            self.slicing_criterion.add(original_node.test.left.value.value)
                            self.slicing_criterion.add(original_node.test.left.attr.value) 
                        else: self.slicing_criterion.add(original_node.test.left.value)
                    # TODO: Make these if-else better
                    # the next one for is if p.name IN blabla
                    if isinstance(original_node.test, cst.Comparison) and hasattr(original_node.test, "comparisons") and isinstance(original_node.test.comparisons[0].comparator, cst.Name) and original_node.test.comparisons[0].comparator.value not in self.slicing_criterion:
                        self.slicing_criterion.add(original_node.test.comparisons[0].comparator.value)
                    if isinstance(original_node.test, cst.BooleanOperation):
                        if original_node.test.left.left.value not in self.slicing_criterion:
                            self.slicing_criterion.add(original_node.test.left.left.value)
                        if original_node.test.right.left.value not in self.slicing_criterion:
                            self.slicing_criterion.add(original_node.test.right.left.value)
                elif self.else_required and not self.if_required:
                    self.if_information.append(int(location.start.line))
        
        # Remove any print statements ig?
        for i in range(len(original_node.body.body)):
            body  = original_node.body.body[i].body[0]
            if isinstance(body, cst.Expr) and isinstance(body.value, cst.Call) and body.value.func.value == 'print' and (int(location.start.line)+i+1) in self.if_information:
                self.if_information = [x for x in self.if_information if x!= (int(location.start.line)+i+1)]
        
        # Remove else lines if its not required
        if not self.else_required:
            self.if_information = [x for x in self.if_information if x not in self.remove_information]
        return updated_node    
    
    def leave_Else_body(self, node: "Else") -> None:
        location = self.get_metadata(PositionProvider, node)
        if isinstance(node.body.body[0], cst.SimpleStatementLine):
            body = node.body.body[0].body[0]
            if isinstance(body, cst.AugAssign):
                value = body.target.value
                # To handle condition where if would add the entire if-else block to if_info but else block is not needed
                if value not in self.slicing_criterion:
                    self.remove_information.extend(range(int(location.start.line), int(location.end.line)+1))
                else:
                    self.if_information.extend(range(int(location.start.line), int(location.end.line)+1))
                    self.else_required = True
        
        if not self.else_required:
            self.remove_information.extend(range(int(location.start.line), int(location.end.line)+1))
                      
    def get_if_information(self):
        return self.if_information, self.slicing_criterion

class GetWhileInformation(cst.CSTTransformer):
    """
    Returns the if information
    """
    
    METADATA_DEPENDENCIES = (
        PositionProvider,
        ParentNodeProvider,
    )
    
    def __init__(self, slicing_criterion: set) -> None:
        super().__init__()
        self.while_information = []
        self.slicing_criterion = slicing_criterion
    
    def leave_While(
        self, original_node: "While", updated_node: "While"
    ) -> Union["BaseStatement", FlattenSentinel["BaseStatement"], cst.RemovalSentinel]:
        location = self.get_metadata(PositionProvider, original_node)
        for i in range(len(original_node.body.body)):
            if isinstance(original_node.body.body[i], cst.SimpleStatementLine):
                body  = original_node.body.body[i].body[0]
                value = ''
                if isinstance(body, cst.Expr) and hasattr(body.value.func, 'attr') and body.value.func.attr.value == 'append':
                    value = body.value.func.value.value
                if isinstance(body, cst.Expr) and hasattr(body.value.func, 'dot'):
                    value = body.value.func.value.value
                if isinstance(body, cst.AugAssign):
                    if isinstance(body.target.value, cst.Name):
                        value = body.target.value.value
                    else: value = body.target.value
                if isinstance(body, cst.Assign) and isinstance(body.targets[0], cst.AssignTarget):
                    value = body.targets[0].target.value.value  #for cases like p.name = something, we set value to p
            if value in self.slicing_criterion:
                self.while_information.extend(range(int(location.start.line), int(location.end.line)+1))
                if isinstance(original_node.test, cst.Comparison) and original_node.test.left.value not in self.slicing_criterion:
                    if hasattr(original_node.test.left, "attr"):
                        self.slicing_criterion.add(original_node.test.left.value.value)
                        self.slicing_criterion.add(original_node.test.left.attr.value) 
                    else: self.slicing_criterion.add(original_node.test.left.value)
        
        # Remove any print statements ig?
        for i in range(len(original_node.body.body)):
            body  = original_node.body.body[i].body[0]
            if isinstance(body, cst.Expr) and isinstance(body.value, cst.Call) and body.value.func.value == 'print' and (int(location.start.line)+i+1) in self.while_information:
                self.while_information = [x for x in self.while_information if x!= (int(location.start.line)+i+1)]
        return updated_node

    def get_while_information(self):
        return self.while_information, self.slicing_criterion


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

def slicing_criterion(code: str) -> tuple[set, int]:
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    
    slicing_criterion_location = SlicingCriterionLocation()
    scl_ayntax_tree = wrapper.visit(slicing_criterion_location)
    
    slicing_criterion = SlicingCriterion(slicing_criterion_location.get_slicing_criterion_location())
    sc_synyax_tree = wrapper.visit(slicing_criterion)
    return slicing_criterion.get_slicing_criterion(), slicing_criterion_location.get_slicing_criterion_location()

def class_information(code: str):
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    get_class_info = GetClassInformation()
    syntax_tree = wrapper.visit(get_class_info)
    return get_class_info.class_info()

def if_information(code: str, criterion: set):
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    get_if_info = GetIfInformation(criterion)
    new_syntax_tree = wrapper.visit(get_if_info)
    # print("new_syntax_tree.code:", new_syntax_tree.code)
    return get_if_info.get_if_information()

def while_information(code: str, criterion: set):
    syntax_tree = cst.parse_module(code)
    wrapper = cst.metadata.MetadataWrapper(syntax_tree)
    get_while_info = GetWhileInformation(criterion)
    new_syntax_tree = wrapper.visit(get_while_info)
    # print("new_syntax_tree.code:", new_syntax_tree.code)
    return get_while_info.get_while_information()

# original_code = """def slice_me():
#     x = 5
#     print("Hello World")  
#     if x < 10:
#         x += 5
#     else:
#         a = b
#     y = 0
#     return y # slicing criterion

# slice_me()
# """

# lines_to_keep = [1, 3, 4, 5, 8]
# x = remove_lines(original_code, lines_to_keep)
# print(x)


# original_code = """def slice_me():
#     german_greetings = ['Hallo', 'Guten Morgen']
#     english_greetings = ['Hello', 'Good morning']
#     translation = f"{german_greetings[0]} is {english_greetings[0]}"
#     greeting = f"{english_greetings[0]}, World!"
#     return greeting # slicing criterion

# slice_me()
# """

# original_code = """class Person:
#     def __init__(self, name):
#         self.name = name

# def slice_me():
#     p = Person('Nobody')
#     indefinite_pronouns = ['Everybody', 'Somebody', 'Nobody', 'Anybody']
#     indefinite_name = p.name in indefinite_pronouns
#     return p.name # slicing criterion

# # slice_me()"""

# original_code = """def slice_me():
#     ages = [0, 25, 50, 75, 100]
#     smallest_age = ages[0]
#     middle_age = ages[2]
#     highest_age = ages[-1]
#     new_highest_age = middle_age + highest_age
#     ages[-1] = 150 # slicing criterion
#     return ages

# slice_me()"""

# y = slicing_criterion(original_code)
# print(y)

# lines_to_keep = [1, 3, 5, 6, 8]
# x = remove_lines(original_code, lines_to_keep)
# print(x)

# y = class_information(original_code)
# print(y)

# original_code = """def slice_me():
#     p = Person('Nobody')
#     indefinite_pronouns = ['Everybody', 'Somebody', 'Nobody', 'Anybody']
#     if p.name in indefinite_pronouns:
#         p.name = "Undefined"
#         print("A person's name should not be an indefinite pronoun.")
#     tries_left = 3
#     while (p.name in indefinite_pronouns or p.name == "Undefined") and tries_left > 0:
#         print("Choose a proper name")
#         tries_left -= 1
#     return p.name # slicing criterion

# slice_me()"""

# y = if_information(original_code, {"p.name", "p", "name"})
# lines, slicing = y
# print(lines, slicing)

# original_code = """class Person:
#     def __init__(self, name):
#         self.name = name
#         self.age = 0

#     def increase_age(self, years):
#         self.age += years
            
# def slice_me():
#     p = Person('Nobody')
#     while p.age < 18:
#         p.increase_age(1)
#     if p.age == 18:
#         print(f'{p.name} is {p.age}')
#     return p # slicing criterion

# slice_me()"""

# y = while_information(original_code, {'p'})
# lines, slicing = y
# print(lines, slicing)