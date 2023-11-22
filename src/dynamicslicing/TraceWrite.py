from typing import List, Callable, Any
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
import logging

class TraceWrite(BaseAnalysis):
    def __init__(self) -> None:
        super().__init__()
        self.danger_of_recursion = False
        logging.basicConfig(filename='output.log', format='%(message)s', encoding='utf-8', level=logging.INFO)
    
    def log(self, iid: int, messsage:str, new_val: Any):
        res = ''
        for arg in args:
            if self.danger_of_recursion:
                res += ' ' + str(hex(id(arg)))
            else:
                res += ' ' + str(arg)
        logging.info(str(iid) + ': ' + res[:80] + 'new_val:'+ str(new_val))

    def write(
        self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any
    ) -> Any:
        self.log(iid, "Writing: ", new_val)