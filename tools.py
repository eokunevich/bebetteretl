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
    def __init__(self, file_path: str, file_format: str = 'csv'):
        super().__init__()
        self.file_path = file_path
        self.file_format = file_format.lower()

    def execute(self):
        if self.input_data is None:
            return None

        if self.file_format == 'csv':
            self.input_data.to_csv(self.file_path, index=False)
        elif self.file_format == 'excel':
            self.input_data.to_excel(self.file_path, index=False)
        elif self.file_format == 'json':
            self.input_data.to_json(self.file_path, orient='records')
        else:
            raise ValueError(f"Unsupported file format: {self.file_format}")

        self.output_data = self.input_data
        return self.output_data

class AggregateTool(ETLTool):
    def __init__(self, aggregations: Dict[str, List[str]], group_by: Optional[str] = None):
        super().__init__()
        self.aggregations = aggregations  # Dict of column name to list of aggregation functions
        self.group_by = group_by

    def execute(self):
        if self.input_data is None:
            return None

        # Create a copy of the input data
        result = self.input_data.copy()

        # If group_by is specified, group the data first
        if self.group_by:
            grouped = result.groupby(self.group_by)
        else:
            grouped = result

        # Apply aggregations
        agg_dict = {}
        for column, functions in self.aggregations.items():
            for func in functions:
                agg_name = f"{column}_{func}"
                if func == "sum":
                    agg_dict[agg_name] = grouped[column].sum()
                elif func == "max":
                    agg_dict[agg_name] = grouped[column].max()
                elif func == "min":
                    agg_dict[agg_name] = grouped[column].min()
                elif func == "mean":
                    agg_dict[agg_name] = grouped[column].mean()
                elif func == "median":
                    agg_dict[agg_name] = grouped[column].median()
                elif func == "count":
                    agg_dict[agg_name] = grouped[column].count()

        # Create the aggregated DataFrame
        self.output_data = pd.DataFrame(agg_dict)
        
        # If group_by was used, reset the index to make it a column
        if self.group_by:
            self.output_data.reset_index(inplace=True)
            
        return self.output_data 