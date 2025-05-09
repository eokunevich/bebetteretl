import pandas as pd
from typing import List, Dict, Any, Optional

class ETLTool:
    def __init__(self):
        self.input_data = None
        self.output_data = None

    def execute(self):
        raise NotImplementedError("Each tool must implement execute method")

class InputTool(ETLTool):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def execute(self):
        self.output_data = pd.read_csv(self.file_path)
        return self.output_data

class SelectTool(ETLTool):
    def __init__(self, columns: List[str], drop_columns: bool = False):
        super().__init__()
        self.columns = columns
        self.drop_columns = drop_columns

    def execute(self):
        if self.drop_columns:
            self.output_data = self.input_data.drop(columns=self.columns)
        else:
            self.output_data = self.input_data[self.columns]
        return self.output_data

class FilterTool(ETLTool):
    def __init__(self, condition: str):
        super().__init__()
        self.condition = condition

    def execute(self):
        self.output_data = self.input_data.query(self.condition)
        return self.output_data

class JoinTool(ETLTool):
    def __init__(self, right_data: pd.DataFrame, how: str = 'inner', 
                 left_on: str = None, right_on: str = None):
        super().__init__()
        self.right_data = right_data
        self.how = how
        self.left_on = left_on
        self.right_on = right_on

    def execute(self):
        self.output_data = pd.merge(
            self.input_data,
            self.right_data,
            how=self.how,
            left_on=self.left_on,
            right_on=self.right_on
        )
        return self.output_data

class MergeTool(ETLTool):
    def __init__(self, additional_data: List[pd.DataFrame]):
        super().__init__()
        self.additional_data = additional_data

    def execute(self):
        all_data = [self.input_data] + self.additional_data
        self.output_data = pd.concat(all_data, ignore_index=True)
        return self.output_data

class FormulaTool(ETLTool):
    def __init__(self, formula: str, new_column: str):
        super().__init__()
        self.formula = formula
        self.new_column = new_column

    def execute(self):
        self.output_data = self.input_data.copy()
        self.output_data[self.new_column] = self.input_data.eval(self.formula)
        return self.output_data

class OutputTool(ETLTool):
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def execute(self):
        self.output_data = self.input_data
        self.output_data.to_csv(self.file_path, index=False)
        return self.output_data 