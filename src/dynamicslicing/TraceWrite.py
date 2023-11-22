from typing import List, Callable, Any
from dynapyt.analyses.BaseAnalysis import BaseAnalysis
import logging

class TraceWrite(BaseAnalysis):
    def __init__(self) -> None:
        super().__init__()
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(handler)
    
    def log(self, iid: int, messsage:str, new_val: Any):
        logging.info(str(new_val))

    def write(
        self, dyn_ast: str, iid: int, old_vals: List[Callable], new_val: Any
    ) -> Any:
        self.log(iid, "Writing: ", new_val)