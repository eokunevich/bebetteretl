import sys
import uuid
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene,
                            QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent,
                            QFileDialog, QMessageBox, QDialog, QLineEdit, QFormLayout,
                            QPushButton, QLabel, QGraphicsPathItem, QListWidgetItem,
                            QCheckBox, QScrollArea, QFrame, QComboBox, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QPainter, QLinearGradient
from workflow_manager import WorkflowManager
from tools import *
from preview_window import PreviewWindow

# Define colors for different tool types
TOOL_COLORS = {
    "Input": QColor(144, 238, 144),  # Light green
    "Select": QColor(173, 216, 230),  # Light blue
    "Filter": QColor(255, 218, 185),  # Peach
    "Join": QColor(221, 160, 221),    # Plum
    "Merge": QColor(255, 228, 196),   # Bisque
    "Formula": QColor(176, 224, 230), # Powder blue
    "Output": QColor(255, 182, 193),   # Light pink
    "Browse": QColor(255, 255, 255)    # White
}

class GridBackground(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 20
        self.setZValue(-1)

    def boundingRect(self):
        return QRectF(-10000, -10000, 20000, 20000)

    def paint(self, painter, option, widget):
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DotLine))
        
        # Draw vertical lines
        for x in range(-10000, 10000, self.grid_size):
            painter.drawLine(x, -10000, x, 10000)
        
        # Draw horizontal lines
        for y in range(-10000, 10000, self.grid_size):
            painter.drawLine(-10000, y, 10000, y)

class FieldListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
        """)

class SelectToolDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Select Tool")
        self.setMinimumWidth(600)  # Increased width to accommodate type column
        self.setMinimumHeight(500)
        
        # Define common styles
        self.label_style = """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: black;
                padding: 5px;
            }
        """
        
        self.button_style = """
            QPushButton {
                padding: 6px 12px;
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                border-radius: 4px;
                color: black;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """
        
        self.input_style = """
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: black;
                font-weight: bold;
                background-color: #f8f9fa;
            }
        """
        
        self.combo_style = """
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: black;
                font-weight: bold;
                background-color: #f8f9fa;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ccc;
                selection-background-color: #e9ecef;
                selection-color: black;
                color: black;
                font-weight: bold;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px;
                color: black;
                font-weight: bold;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e9ecef;
                color: black;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e9ecef;
                color: black;
            }
        """
        
        layout = QVBoxLayout()
        
        # Add header label
        header_label = QLabel("Select and Configure Fields")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: black;
                padding: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Create scroll area for fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        
        # Create widget to hold field list
        field_widget = QWidget()
        field_layout = QVBoxLayout(field_widget)
        
        # Add column headers
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        
        include_label = QLabel("Include")
        field_name_label = QLabel("Field Name")
        field_type_label = QLabel("Type")
        rename_label = QLabel("Rename To")
        
        for label in [include_label, field_name_label, field_type_label, rename_label]:
            label.setStyleSheet(self.label_style)
        
        header_layout.addWidget(include_label, 0)
        header_layout.addWidget(field_name_label, 1)
        header_layout.addWidget(field_type_label, 1)
        header_layout.addWidget(rename_label, 1)
        field_layout.addWidget(header_frame)
        
        # Add fields with checkboxes and rename options
        self.field_checkboxes = {}
        self.field_renames = {}
        self.field_types = {}
        
        for column in columns:
            field_frame = QFrame()
            field_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #eee;
                    border-radius: 4px;
                    margin: 2px;
                }
                QCheckBox {
                    padding: 4px;
                }
                QLabel {
                    color: black;
                    font-weight: bold;
                }
            """)
            field_layout_inner = QHBoxLayout(field_frame)
            
            # Checkbox for selecting field
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.field_checkboxes[column] = checkbox
            field_layout_inner.addWidget(checkbox, 0)
            
            # Original field name
            field_name = QLabel(column)
            field_name.setStyleSheet(self.label_style)
            field_layout_inner.addWidget(field_name, 1)
            
            # Field type dropdown
            type_combo = QComboBox()
            type_combo.addItems(["String", "Integer", "Float", "Date", "Boolean"])
            type_combo.setStyleSheet(self.combo_style)
            self.field_types[column] = type_combo
            field_layout_inner.addWidget(type_combo, 1)
            
            # Rename field input
            rename_input = QLineEdit()
            rename_input.setText(column)  # Default to original name
            rename_input.setPlaceholderText("Enter new name...")
            rename_input.setStyleSheet(self.input_style)
            self.field_renames[column] = rename_input
            field_layout_inner.addWidget(rename_input, 1)
            
            field_layout.addWidget(field_frame)
        
        scroll.setWidget(field_widget)
        layout.addWidget(scroll)
        
        # Add buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        # Style buttons
        for btn in [select_all_btn, deselect_all_btn, ok_button, cancel_button]:
            btn.setStyleSheet(self.button_style)
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn.clicked.connect(self.deselect_all)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
    
    def select_all(self):
        for checkbox in self.field_checkboxes.values():
            checkbox.setChecked(True)
    
    def deselect_all(self):
        for checkbox in self.field_checkboxes.values():
            checkbox.setChecked(False)
    
    def get_selected_fields(self):
        selected_fields = {}
        for original_name, checkbox in self.field_checkboxes.items():
            if checkbox.isChecked():
                new_name = self.field_renames[original_name].text().strip()
                field_type = self.field_types[original_name].currentText()
                if new_name:  # Only include if new name is not empty
                    selected_fields[original_name] = {
                        'new_name': new_name,
                        'type': field_type
                    }
        return selected_fields

class FilterToolDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Filter Tool")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Add header
        header_label = QLabel("Configure Filter Condition")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: black;
                padding: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Create form layout for dropdowns
        form_layout = QFormLayout()
        
        # Field dropdown
        self.field_combo = QComboBox()
        self.field_combo.addItems(columns)
        self.field_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f8f9fa;
                color: black;
                font-weight: bold;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        form_layout.addRow("Field:", self.field_combo)
        
        # Operator dropdown
        self.operator_combo = QComboBox()
        operators = [
            "equals",
            "not equal",
            "greater than",
            "greater than or equal",
            "less than",
            "less than or equal",
            "contains"
        ]
        self.operator_combo.addItems(operators)
        self.operator_combo.setStyleSheet(self.field_combo.styleSheet())
        form_layout.addRow("Operator:", self.operator_combo)
        
        # Value input
        self.value_input = QLineEdit()
        self.value_input.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f8f9fa;
                color: black;
                font-weight: bold;
            }
        """)
        form_layout.addRow("Value:", self.value_input)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        for btn in [ok_button, cancel_button]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 6px 12px;
                    background-color: #f8f9fa;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    color: black;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
    
    def get_filter_condition(self):
        field = self.field_combo.currentText()
        operator = self.operator_combo.currentText()
        value = self.value_input.text()
        
        # Convert operator to pandas query syntax
        operator_map = {
            "equals": "==",
            "not equal": "!=",
            "greater than": ">",
            "greater than or equal": ">=",
            "less than": "<",
            "less than or equal": "<=",
            "contains": ".str.contains"
        }
        
        if operator == "contains":
            return f"{field}.str.contains('{value}')"
        else:
            return f"{field} {operator_map[operator]} '{value}'"

class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_node, end_node):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.setPen(QPen(QColor(100, 100, 100), 2))
        self.setZValue(0)
        self.update_path()
        self.setAcceptHoverEvents(True)
        self.is_hovered = False

    def update_path(self):
        path = QPainterPath()
        start_pos = self.start_node.pos() + QPointF(60, 25)
        end_pos = self.end_node.pos() + QPointF(60, 25)
        
        # Create a curved path
        control_point1 = QPointF(start_pos.x() + (end_pos.x() - start_pos.x()) * 0.5, start_pos.y())
        control_point2 = QPointF(start_pos.x() + (end_pos.x() - start_pos.x()) * 0.5, end_pos.y())
        
        path.moveTo(start_pos)
        path.cubicTo(control_point1, control_point2, end_pos)
        
        self.setPath(path)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.setPen(QPen(QColor(0, 120, 215), 3))  # Highlight color
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.setPen(QPen(QColor(100, 100, 100), 2))
        self.update()
        super().hoverLeaveEvent(event)

class BrowseToolDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Browse Data")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout()
        
        # Add header
        header_label = QLabel("Data Preview")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: black;
                padding: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
                color: black;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
        """)
        
        # Populate table with data
        if data is not None:
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(data.columns))
            self.table.setHorizontalHeaderLabels(data.columns)
            
            # Fill data
            for i in range(len(data)):
                for j in range(len(data.columns)):
                    item = QTableWidgetItem(str(data.iloc[i, j]))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                    self.table.setItem(i, j, item)
        
        layout.addWidget(self.table)
        
        # Add buttons
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                border-radius: 4px;
                color: black;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        close_button.clicked.connect(self.accept)

class ToolNode(QGraphicsItem):
    def __init__(self, tool_type, parent=None):
        super().__init__(parent)
        self.tool_type = tool_type
        self.node_id = str(uuid.uuid4())
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.width = 120
        self.height = 50
        self.setZValue(1)
        self.properties = {}
        self.input_data = None
        self.output_data = None
        self.connections = []
        self.is_hovered = False
        self.input_ports = []
        self.output_ports = []

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        # Create gradient for node background
        gradient = QLinearGradient(0, 0, 0, self.height)
        base_color = TOOL_COLORS.get(self.tool_type, QColor(200, 200, 200))
        
        if self.is_hovered:
            gradient.setColorAt(0, base_color.lighter(120))
            gradient.setColorAt(1, base_color.lighter(140))
        else:
            gradient.setColorAt(0, base_color)
            gradient.setColorAt(1, base_color.darker(110))

        # Draw node background
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)

        # Draw node text
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(QRectF(0, 0, self.width, self.height), 
                        Qt.AlignmentFlag.AlignCenter, self.tool_type)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Show connection menu
            menu = QMenu()
            connect_menu = menu.addMenu("Connect to...")
            
            # Add available tools as submenu items
            available_tools = ["Input", "Select", "Filter", "Join", "Merge", "Formula", "Output", "Browse"]
            for tool in available_tools:
                # Don't allow connecting to the same tool type
                if tool != self.tool_type:
                    action = connect_menu.addAction(tool)
                    action.triggered.connect(lambda checked, t=tool: self.create_connection(t))
            
            # Add other menu items
            configure_action = menu.addAction("Configure")
            preview_action = menu.addAction("Preview Data")
            delete_action = menu.addAction("Delete")
            
            # Show menu at cursor position
            action = menu.exec(event.screenPos())
            
            if action == configure_action:
                self.configure_tool()
            elif action == preview_action:
                self.preview_data()
            elif action == delete_action:
                self.delete_node()
        
        super().mousePressEvent(event)

    def create_connection(self, target_tool_type):
        # Create a new node of the target type
        target_node = ToolNode(target_tool_type)
        # Position it to the right of the current node
        target_node.setPos(self.pos() + QPointF(200, 0))
        self.scene().addItem(target_node)
        
        # Create connection
        connection = ConnectionLine(self, target_node)
        self.scene().addItem(connection)
        self.scene().connections.append(connection)
        self.connections.append(connection)
        target_node.connections.append(connection)
        
        # Pass data to the new node
        target_node.input_data = self.output_data
        
        # Configure the new node if it's a Select tool and we have data
        if target_tool_type == "Select" and self.output_data is not None:
            target_node.configure_tool()
        
        # Add to workflow manager
        self.scene().workflow_manager.add_node(
            target_node.node_id,
            target_node.tool_type,
            {'x': target_node.pos().x(), 'y': target_node.pos().y()},
            target_node.properties
        )

    def configure_tool(self):
        if self.tool_type == "Browse":
            if self.input_data is None:
                # Check if we have a connection and get data from the source node
                for conn in self.connections:
                    if conn.end_node == self:
                        self.input_data = conn.start_node.output_data
                        break
            
            if self.input_data is not None:
                dialog = BrowseToolDialog(self.input_data, self.scene().views()[0])
                dialog.exec()
            else:
                QMessageBox.warning(self.scene().views()[0], "No Input Data", 
                                  "Please connect to a data source first.")
            return

        elif self.tool_type == "Select":
            if self.input_data is None:
                # Check if we have a connection and get data from the source node
                for conn in self.connections:
                    if conn.end_node == self:
                        self.input_data = conn.start_node.output_data
                        break
            
            if self.input_data is not None and hasattr(self.input_data, 'columns'):
                dialog = SelectToolDialog(self.input_data.columns, self.scene().views()[0])
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.properties['columns'] = dialog.get_selected_fields()
                    self.execute_tool()
            else:
                QMessageBox.warning(self.scene().views()[0], "No Input Data", 
                                  "Please connect to an Input tool and configure it first.")
            return

        elif self.tool_type == "Filter":
            if self.input_data is None:
                # Check if we have a connection and get data from the source node
                for conn in self.connections:
                    if conn.end_node == self:
                        self.input_data = conn.start_node.output_data
                        break
            
            if self.input_data is not None and hasattr(self.input_data, 'columns'):
                dialog = FilterToolDialog(self.input_data.columns, self.scene().views()[0])
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.properties['condition'] = dialog.get_filter_condition()
                    self.execute_tool()
            else:
                QMessageBox.warning(self.scene().views()[0], "No Input Data", 
                                  "Please connect to an Input tool and configure it first.")
            return

        dialog = QDialog(self.scene().views()[0])
        dialog.setWindowTitle(f"Configure {self.tool_type} Tool")
        layout = QFormLayout(dialog)

        if self.tool_type == "Input":
            file_path = QLineEdit()
            browse_button = QPushButton("Browse")
            layout.addRow("File Path:", file_path)
            layout.addRow(browse_button)
            
            def browse_file():
                path, _ = QFileDialog.getOpenFileName(dialog, "Select Input File", "", 
                                                    "CSV Files (*.csv);;All Files (*)")
                if path:
                    file_path.setText(path)
                    self.properties['file_path'] = path
                    # Load and preview data immediately
                    try:
                        self.output_data = pd.read_csv(path)
                        # Update connected nodes
                        for conn in self.connections:
                            if conn.start_node == self:
                                conn.end_node.input_data = self.output_data
                        self.preview_data()
                    except Exception as e:
                        QMessageBox.critical(dialog, "Error", f"Error loading file: {str(e)}")
            
            browse_button.clicked.connect(browse_file)

        elif self.tool_type == "Output":
            file_path = QLineEdit()
            browse_button = QPushButton("Browse")
            layout.addRow("Output File Path:", file_path)
            layout.addRow(browse_button)
            
            def browse_file():
                path, _ = QFileDialog.getSaveFileName(dialog, "Select Output File", "", 
                                                    "CSV Files (*.csv);;All Files (*)")
                if path:
                    file_path.setText(path)
                    self.properties['file_path'] = path
            
            browse_button.clicked.connect(browse_file)

        # Add buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.execute_tool()

    def preview_data(self):
        if self.output_data is not None:
            preview = PreviewWindow(self.output_data, self.scene().views()[0])
            preview.exec()
        else:
            QMessageBox.information(self.scene().views()[0], "No Data", 
                                  "No data available to preview. Configure the tool first.")

    def delete_node(self):
        # Remove all connections
        for connection in self.connections:
            self.scene().removeItem(connection)
        self.scene().removeItem(self)

    def execute_tool(self):
        if self.tool_type == "Input":
            try:
                self.output_data = pd.read_csv(self.properties['file_path'])
            except Exception as e:
                QMessageBox.critical(self.scene().views()[0], "Error", f"Error loading file: {str(e)}")
        elif self.tool_type == "Select" and self.input_data is not None:
            try:
                # Get selected fields with their new names and types
                selected_fields = self.properties['columns']
                # Create a copy of the input data with selected columns
                self.output_data = self.input_data[list(selected_fields.keys())].copy()
                
                # Rename columns
                rename_dict = {old: info['new_name'] for old, info in selected_fields.items()}
                self.output_data.rename(columns=rename_dict, inplace=True)
                
                # Convert types
                for old_name, info in selected_fields.items():
                    new_name = info['new_name']
                    field_type = info['type']
                    try:
                        if field_type == "Integer":
                            self.output_data[new_name] = pd.to_numeric(self.output_data[new_name], downcast='integer')
                        elif field_type == "Float":
                            self.output_data[new_name] = pd.to_numeric(self.output_data[new_name], downcast='float')
                        elif field_type == "Date":
                            self.output_data[new_name] = pd.to_datetime(self.output_data[new_name])
                        elif field_type == "Boolean":
                            self.output_data[new_name] = self.output_data[new_name].astype(bool)
                        # String is the default, no conversion needed
                    except Exception as e:
                        QMessageBox.warning(self.scene().views()[0], "Type Conversion Warning",
                                          f"Could not convert {new_name} to {field_type}: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self.scene().views()[0], "Error", f"Error selecting/renaming columns: {str(e)}")
        elif self.tool_type == "Filter" and self.input_data is not None:
            try:
                condition = self.properties['condition']
                self.output_data = self.input_data.query(condition)
            except Exception as e:
                QMessageBox.critical(self.scene().views()[0], "Error", f"Error applying filter: {str(e)}")
        elif self.tool_type == "Browse":
            self.output_data = self.input_data

class WorkflowScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-10000, -10000, 20000, 20000)
        self.workflow_manager = WorkflowManager()
        self.connections = []
        
        # Add grid background
        self.grid = GridBackground()
        self.addItem(self.grid)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Be Better ETL")
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Create tools panel with styled list
        tools_panel = QListWidget()
        tools_panel.setMaximumWidth(200)
        tools_panel.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                color: black;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #e0e0e0;
            }
        """)

        # Add color-coded tool items
        tools = ["Input", "Select", "Filter", "Join", "Merge", "Formula", "Output", "Browse"]
        for tool in tools:
            item = QListWidgetItem(tool)
            color = TOOL_COLORS.get(tool, QColor(200, 200, 200))
            item.setBackground(QBrush(color))
            item.setForeground(QBrush(QColor(0, 0, 0)))  # Black text
            tools_panel.addItem(item)

        layout.addWidget(tools_panel)

        # Create workflow canvas with styled view
        self.scene = WorkflowScene()
        self.view = QGraphicsView(self.scene)
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        layout.addWidget(self.view)

        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        save_action = file_menu.addAction("Save Workflow")
        save_action.triggered.connect(self.save_workflow)
        
        load_action = file_menu.addAction("Load Workflow")
        load_action.triggered.connect(self.load_workflow)
        
        run_action = file_menu.addAction("Run Workflow")
        run_action.triggered.connect(self.run_workflow)

        # Connect signals
        tools_panel.itemDoubleClicked.connect(self.add_tool_to_workflow)

    def add_tool_to_workflow(self, item):
        tool_node = ToolNode(item.text())
        self.scene.addItem(tool_node)
        tool_node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.workflow_manager.add_node(
            tool_node.node_id,
            tool_node.tool_type,
            {'x': tool_node.pos().x(), 'y': tool_node.pos().y()},
            tool_node.properties
        )

    def save_workflow(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Workflow", "", 
                                                 "Workflow Files (*.json);;All Files (*)")
        if file_path:
            self.scene.workflow_manager.save_workflow(file_path)

    def load_workflow(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Workflow", "", 
                                                 "Workflow Files (*.json);;All Files (*)")
        if file_path:
            self.scene.clear()
            self.scene.workflow_manager.load_workflow(file_path)
            self.recreate_workflow()

    def recreate_workflow(self):
        # Clear existing items
        self.scene.clear()
        self.scene.connections = []

        # Recreate nodes
        nodes = {}
        for node_id, node_data in self.scene.workflow_manager.nodes.items():
            tool_node = ToolNode(node_data['type'])
            tool_node.node_id = node_id
            tool_node.properties = node_data['properties']
            tool_node.setPos(node_data['position']['x'], node_data['position']['y'])
            self.scene.addItem(tool_node)
            nodes[node_id] = tool_node

        # Recreate connections
        for connection in self.scene.workflow_manager.connections:
            start_node = nodes[connection['from']]
            end_node = nodes[connection['to']]
            connection_line = ConnectionLine(start_node, end_node)
            self.scene.addItem(connection_line)
            self.scene.connections.append(connection_line)
            start_node.connections.append(connection_line)
            end_node.connections.append(connection_line)

    def run_workflow(self):
        try:
            tools = self.scene.workflow_manager.execute_workflow()
            QMessageBox.information(self, "Success", "Workflow executed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error executing workflow: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 