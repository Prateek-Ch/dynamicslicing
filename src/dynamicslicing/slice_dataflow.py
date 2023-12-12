import libcst as cst
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
from dynapyt.instrument.IIDs import IIDs
from utils import slicing_criterion, remove_lines
from typing import List, Callable, Any, Tuple, Dict
from dynapyt.utils.nodeLocator import get_node_by_location
import argparse

class SliceDataflow(BaseAnalysis):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--directory', dest='directory', type=str, help='Instrumentation to slice')
        parser.add_argument('--analysis', dest='analysis', type=str, help='Add analysis to slice')
        parser.add_argument('--entry', dest='entry', type=str, help='Add entry to slice')
        args = parser.parse_args()
        
        with open(args.entry, "r") as file:
            self.source = file.read()
        iid_object = IIDs(args.entry)
        
        self.asts = {}
        self.slice_criteria = slicing_criterion(self.source)
        self.dependencies = set()
        self.line_numbers = List[int]
        
    def add_node_to_dependencies(self, node: Any, location: int):
        if isinstance(node, cst.Name):
            if node.value == self.slice_criteria and location not in self.line_numbers:
                self.line_numbers.append(location)
                self.dependencies.add(node)
        elif isinstance(node, cst.Assign):
            if node.targets[0].target.value == self.slice_criteria and location not in self.line_numbers:
                self.line_numbers.append(location)
                self.dependencies.add(node)
        elif isinstance(node, cst.AugAssign):
            if node.target.value == self.slice_criteria and location not in self.line_numbers:
                self.line_numbers.append(location)
                self.dependencies.add(node)
    
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
            self.line_numbers.append(location.start_line)
            self.dependencies.add(node)
    
    def end_execution(self) -> None:
        sliced_code = remove_lines(self.source, self.line_numbers)
        print(sliced_code)
    
 

