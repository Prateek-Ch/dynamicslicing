import libcst as cst
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from dynamicslicing.utils import slicing_criterion, remove_lines, class_information, if_information, while_information
from typing import List, Callable, Any, Tuple, Dict
from dynapyt.utils.nodeLocator import get_node_by_location
import os

class Slice(BaseAnalysis):
    def __init__(self, source):
        super().__init__()
        self.args = source
        self.initialize_slice_data()
    
    def initialize_slice_data(self):
        self.read_source_file()
        self.extract_slice_criteria()

    def read_source_file(self):
        file_name = f"{self.args}"
        with open(file_name, "r") as file:
            self.source = file.read()

    def extract_slice_criteria(self):
        set_slice_criterion = slicing_criterion(self.source)
        self.slice_criteria = set_slice_criterion[0]
        self.slicing_criterion_location = set_slice_criterion[1]
        self.dependencies = set()
        self.node_dict = {}
        self.line_numbers = []
        self.write_values = {}
        class_info = class_information(self.source)
        if class_info:
            self.line_numbers.extend(class_info)
        
    def add_node_to_dependencies(self, node: Any, location: int, type: str):
        if location not in self.line_numbers:
            self.node_dict[location] = {type: node}
        if isinstance(node, cst.Name):
            if node.value in self.slice_criteria and location not in self.line_numbers:
                self.line_numbers.append(location)
                self.dependencies.add(node)
        elif isinstance(node, cst.Assign):
            if isinstance(node.targets[0].target.value, cst.Name) and node.targets[0].target.value.value in self.slice_criteria and location not in self.line_numbers:
                self.line_numbers.append(location)
                self.dependencies.add(node)
            elif node.targets[0].target.value in self.slice_criteria and location not in self.line_numbers:
                temp = node.value
                if isinstance(temp, cst.SimpleString):
                    if temp.evaluated_value == "":
                        return
                self.line_numbers.append(location)
                self.dependencies.add(node)
        elif isinstance(node, cst.AugAssign):
            if node.target.value in self.slice_criteria and location not in self.line_numbers:
                self.line_numbers.append(location)
                self.dependencies.add(node)
    
    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if location.start_line == self.slicing_criterion_location:
            self.add_node_to_dependencies(node, location.start_line, "read")
    
    def write(
        self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any
    ) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if getattr(node.value, 'value', None) or isinstance(node.value, cst.List):
            if hasattr(node, 'targets'):
                if isinstance(node.value, cst.Subscript) and hasattr(node.value.slice[0].slice, "value") and hasattr(node.value.slice[0].slice.value, "value"):
                    lista = node.value.value.value
                    listb = node.value.slice[0].slice.value.value
                    if lista in self.write_values:
                        key = self.write_values[lista]
                        value = key[int(listb)]
                        self.write_values[str(node.targets[0].target.value)] = value
                    else: self.write_values[str(node.targets[0].target.value)] = f"{lista}[{listb}]"
                elif isinstance(node.value, cst.List):
                    elements = [element.value.value for element in node.value.elements]
                    self.write_values[str(node.targets[0].target.value)] = elements
                else:
                    self.write_values[str(node.targets[0].target.value)] = str(node.value.value)
        if isinstance(node, cst.Assign) and node.targets[0].target.value in self.slice_criteria:
            if hasattr(node.value, "parts") and isinstance(node.value.parts[0], cst.FormattedStringExpression):
                self.slice_criteria.add(node.value.parts[0].expression.value.value)
        if location.start_line <= self.slicing_criterion_location:
            self.add_node_to_dependencies(node, location.start_line, "write")
        
    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        result: Any,
        call: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        if location.start_line not in self.line_numbers:
            self.node_dict[location.start_line] = {"post_call": node}
            if node.func.value in self.slice_criteria:
                self.line_numbers.append(location.start_line)
                self.dependencies.add(node)
    
    def function_enter(
        self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool
    ) -> None:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        
        if location.start_line not in self.line_numbers:
            self.node_dict[location.start_line] = {"function_enter": node}
            self.line_numbers.append(location.start_line)
            self.dependencies.add(node)
    
    def pre_call(
        self, dyn_ast: str, iid: int, function: Callable, pos_args: Tuple, kw_args: Dict
    ):
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        func_value, func_attr = '', ''
        if location.start_line not in self.line_numbers:
            if isinstance(node.func, cst.Attribute):
                if node.func.attr.value == "append" and node.func.value.value in self.slice_criteria:
                    self.node_dict[location.start_line] = {"pre_call": node}
                    self.line_numbers.append(location.start_line)
                    self.dependencies.add(node)
            if len(node.args) == 0:
                self.node_dict[location.start_line] = {"pre_call": node}
                self.line_numbers.append(location.start_line)
                self.dependencies.add(node)
    
    def get_value(self, node) -> str:
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Assign):
            if isinstance(node.value, cst.Comparison):
                if isinstance(node.targets[0], cst.AssignTarget):
                    return node.targets[0].target.value
                return node.value.left.value.value
            if isinstance(node.targets[0], cst.AssignTarget):
                if hasattr(node.targets[0].target, "value") and hasattr(node.targets[0].target.value, "value"): 
                    if node.targets[0].target.value.value in self.slice_criteria or node.targets[0].target.attr.value in self.slice_criteria:
                        if hasattr(node.value, "value") and hasattr(node.value.value, "value"):
                            self.slice_criteria.add(node.value.value.value)
                            return node.targets[0].target.value.value
            temp = node.targets[0].target
            if isinstance(temp, cst.Attribute):
                return temp.attr.value       
            return node.targets[0].target.value
        elif isinstance(node, cst.AugAssign):
            return node.target.value
        elif isinstance(node, cst.Call):
            if isinstance(node.func, cst.Attribute) and node.func.value.value in self.slice_criteria and node.func.attr.value == "append":
                if len(node.args) > 0:
                    self.slice_criteria.add(node.args[0].value.value)
                    return node.args[0].value.value
    
    def end_execution(self) -> None:
        # If-Else Information
        lines, slicing, bad_ifs = if_information(self.source, self.slice_criteria, self.write_values)
        self.slice_criteria.update(set(slicing))
        self.line_numbers.extend(x for x in lines if x not in self.line_numbers and x <= self.slicing_criterion_location)
        
        # While Information
        lines, slicing = while_information(self.source, self.slice_criteria)
        self.slice_criteria.update(set(slicing))
        self.line_numbers.extend(x for x in lines if x not in self.line_numbers and x <= self.slicing_criterion_location)
        
        reverse_sorted_dict = dict(sorted(self.node_dict.items(), reverse = True))
        for outer_key, inner_dict in reverse_sorted_dict.items():
            for inner_key, value in inner_dict.items():
                line_number = outer_key
                dtype = inner_key
                node = value
                temp = self.get_value(node)
                if temp in self.slice_criteria and line_number not in self.line_numbers and dtype != "read" and line_number <= self.slicing_criterion_location:
                    if isinstance(node.value, cst.SimpleString) and node.value.evaluated_value == "":
                        pass
                    else:
                        self.line_numbers.append(line_number)
                        if isinstance(node.value, cst.BinaryOperation):
                            self.slice_criteria.add(node.value.left.value)
                            self.slice_criteria.add(node.value.right.value)
        # weird check
        if self.slicing_criterion_location not in self.line_numbers:
            self.line_numbers.append(self.slicing_criterion_location)
            
        self.line_numbers = [x for x in self.line_numbers if x not in bad_ifs]
        sliced_code = remove_lines(self.source, self.line_numbers)
        output_file_name = os.path.join(os.path.dirname(self.args), "sliced.py")
        with open(output_file_name, "w") as output_file:
            output_file.write(sliced_code)