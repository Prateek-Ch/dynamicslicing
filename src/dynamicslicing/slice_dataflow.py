import libcst as cst
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from utils import slicing_criterion
from typing import List, Callable, Any, Tuple, Dict
from dynapyt.utils.nodeLocator import get_node_by_location

class SliceDataflow(BaseAnalysis):
    def __init__(self):
        # with open(source_path, "r") as file:
        #     source = file.read()
        # iid_object = IIDs(source_path)
        # x = slicing_criterion(source)
        # print(x)
        self.asts = {}
        self.slice_criteria = "y"
        self.dependencies = set()
        self.line_numbers = set()
        
    def add_node_to_dependencies(self, node: Any, location: int):
        if isinstance(node, cst.Name):
            if node.value == self.slice_criteria and location not in self.line_numbers:
                print(location)
                self.line_numbers.add(location)
                self.dependencies.add(node)
        elif isinstance(node, cst.Assign):
            if node.targets[0].target.value == self.slice_criteria and location not in self.line_numbers:
                print(location)
                self.line_numbers.add(location)
                self.dependencies.add(node)
        elif isinstance(node, cst.AugAssign):
            if node.target.value == self.slice_criteria and location not in self.line_numbers:
                print(location)
                self.line_numbers.add(location)
                self.dependencies.add(node)
        print("bla", self.line_numbers)
        print("vlsdvs", self.dependencies)
    
    def memory_access(self, dyn_ast: str, iid: int, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        self.add_node_to_dependencies(node, location.start_line)
    
    def read(self, dyn_ast: str, iid: int, val: Any) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        self.add_node_to_dependencies(node, location.start_line)
    
    def write(
        self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any
    ) -> Any:
        location = self.iid_to_location(dyn_ast, iid)
        node = get_node_by_location(self._get_ast(dyn_ast)[0], location)
        self.add_node_to_dependencies(node, location.start_line)
            
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
        if node.func.value == self.slice_criteria and location.start_line not in self.line_numbers:
            self.line_numbers.add(location.start_line)
            self.dependencies.add(node)

# input_file_path = "temp_test.py"
# slicer = SliceDataflow(input_file_path)
if __name__ == "__main__":
    slice_dataflow = SliceDataflow()
    # print("slice df dependencies", slice_dataflow.dependencies)