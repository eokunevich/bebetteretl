from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt
import pandas as pd

class PreviewWindow(QDialog):
    def __init__(self, data: pd.DataFrame, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Preview")
        self.setGeometry(100, 100, 800, 600)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create table
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Add close button
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Populate table with data
        self.populate_table(data)
    
    def populate_table(self, data: pd.DataFrame):
        # Limit to 50 rows
        preview_data = data.head(50)
        
        # Set table dimensions
        self.table.setRowCount(len(preview_data))
        self.table.setColumnCount(len(preview_data.columns))
        
        # Set headers
        self.table.setHorizontalHeaderLabels(preview_data.columns)
        
        # Populate cells
        for i, row in enumerate(preview_data.itertuples()):
            for j, value in enumerate(row[1:]):  # Skip index
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                self.table.setItem(i, j, item)
        
        # Resize columns to content
        self.table.resizeColumnsToContents() 