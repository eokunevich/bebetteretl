import json
import pickle
from typing import Dict, List, Any
from tools import ETLTool

class WorkflowManager:
    def __init__(self):
        self.nodes = {}  # Dictionary to store tool nodes
        self.connections = []  # List to store connections between nodes
        self.node_data = {}  # Dictionary to store data for each node

    def add_node(self, node_id: str, tool_type: str, position: Dict[str, float], 
                properties: Dict[str, Any] = None):
        self.nodes[node_id] = {
            'type': tool_type,
            'position': position,
            'properties': properties or {}
        }

    def add_connection(self, from_node: str, to_node: str):
        self.connections.append({
            'from': from_node,
            'to': to_node
        })

    def remove_node(self, node_id: str):
        """Remove a node and its associated data and connections"""
        # Remove the node
        if node_id in self.nodes:
            del self.nodes[node_id]
        
        # Remove associated data
        if node_id in self.node_data:
            del self.node_data[node_id]
        
        # Remove all connections involving this node
        self.connections = [conn for conn in self.connections 
                          if conn['from'] != node_id and conn['to'] != node_id]

    def remove_connection(self, from_node: str, to_node: str):
        """Remove a connection between two nodes"""
        self.connections = [conn for conn in self.connections 
                          if not (conn['from'] == from_node and conn['to'] == to_node)]

    def get_node_data(self, node_id: str):
        """Get the data associated with a node"""
        return self.node_data.get(node_id)

    def set_node_data(self, node_id: str, data):
        """Set the data for a node"""
        self.node_data[node_id] = data

    def save_workflow(self, file_path: str):
        workflow_data = {
            'nodes': self.nodes,
            'connections': self.connections
        }
        with open(file_path, 'w') as f:
            json.dump(workflow_data, f, indent=2)

    def load_workflow(self, file_path: str):
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)
        self.nodes = workflow_data['nodes']
        self.connections = workflow_data['connections']

    def execute_workflow(self):
        # Create a dictionary to store tool instances
        tools = {}
        
        # First, create all tool instances
        for node_id, node_data in self.nodes.items():
            tool_type = node_data['type']
            properties = node_data['properties']
            
            # Create appropriate tool instance based on type
            if tool_type == 'Input':
                tools[node_id] = InputTool(properties['file_path'])
            elif tool_type == 'Select':
                tools[node_id] = SelectTool(properties['columns'], 
                                          properties.get('drop_columns', False))
            elif tool_type == 'Filter':
                tools[node_id] = FilterTool(properties['condition'])
            elif tool_type == 'Join':
                tools[node_id] = JoinTool(properties['right_data'],
                                        properties.get('how', 'inner'),
                                        properties.get('left_on'),
                                        properties.get('right_on'))
            elif tool_type == 'Merge':
                tools[node_id] = MergeTool(properties['additional_data'])
            elif tool_type == 'Formula':
                tools[node_id] = FormulaTool(properties['formula'],
                                           properties['new_column'])
            elif tool_type == 'Output':
                tools[node_id] = OutputTool(properties['file_path'])
            elif tool_type == 'Aggregate':
                tools[node_id] = AggregateTool(properties['aggregations'],
                                             properties.get('group_by'))

        # Then, execute tools in order based on connections
        for connection in self.connections:
            from_tool = tools[connection['from']]
            to_tool = tools[connection['to']]
            to_tool.input_data = from_tool.output_data
            to_tool.execute()
            # Store the output data
            self.set_node_data(connection['to'], to_tool.output_data)

        return tools 