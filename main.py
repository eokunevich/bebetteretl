import sys
import uuid
import math
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QListWidget, QGraphicsView, QGraphicsScene,
                            QGraphicsItem, QMenu, QGraphicsSceneContextMenuEvent,
                            QFileDialog, QMessageBox, QDialog, QLineEdit, QFormLayout,
                            QPushButton, QLabel, QGraphicsPathItem, QListWidgetItem,
                            QCheckBox, QScrollArea, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
                            QToolTip, QSlider, QToolButton, QGraphicsObject)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QMimeData, QObject
from PyQt6.QtGui import (QPen, QBrush, QColor, QPainterPath, QPainter, QLinearGradient, 
                        QIcon, QFont, QTransform, QPainterPath, QFontMetrics, QDrag)
from workflow_manager import WorkflowManager
from tools import *
from preview_window import PreviewWindow

# Define colors for different tool types
TOOL_COLORS = {
    "Input": QColor(235, 245, 255),  # Light blue
    "Select": QColor(235, 255, 235),  # Light green
    "Filter": QColor(255, 245, 235),  # Light orange
    "Join": QColor(245, 235, 255),    # Light purple
    "Merge": QColor(255, 235, 245),   # Light pink
    "Formula": QColor(235, 255, 245), # Light teal
    "Output": QColor(255, 235, 235),  # Light red
    "Browse": QColor(245, 245, 245),  # Light gray
    "Aggregate": QColor(255, 245, 215) # Light yellow
}

class GridBackground(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_size = 20
        self.setZValue(-1)
        self.major_grid_size = 100  # Size of major grid lines
        self.grid_color = QColor(240, 240, 240)
        self.major_grid_color = QColor(220, 220, 220)

    def boundingRect(self):
        return QRectF(-10000, -10000, 20000, 20000)

    def paint(self, painter, option, widget):
        # Draw major grid lines
        painter.setPen(QPen(self.major_grid_color, 1, Qt.PenStyle.SolidLine))
        for x in range(-10000, 10000, self.major_grid_size):
            painter.drawLine(x, -10000, x, 10000)
        for y in range(-10000, 10000, self.major_grid_size):
            painter.drawLine(-10000, y, 10000, y)

        # Draw minor grid lines
        painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.SolidLine))
        for x in range(-10000, 10000, self.grid_size):
            if x % self.major_grid_size != 0:  # Skip major grid lines
                painter.drawLine(x, -10000, x, 10000)
        for y in range(-10000, 10000, self.grid_size):
            if y % self.major_grid_size != 0:  # Skip major grid lines
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

class ConnectionLine(QGraphicsObject):
    def __init__(self, source_node, target_node):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self._opacity = 1.0
        self.setZValue(-1)  # Draw connections below nodes
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(150)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.7)
        
        # Update path when nodes move
        self.source_node.positionChanged.connect(self.update_path)
        self.target_node.positionChanged.connect(self.update_path)
        self.update_path()
        
    @property
    def opacity(self):
        return self._opacity
        
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()
        
    def update_path(self):
        if not self.source_node or not self.target_node:
            return
            
        # Calculate connection points
        source_pos = self.source_node.pos()
        target_pos = self.target_node.pos()
        
        # Create a path from source to target
        self._path = QPainterPath()
        self._path.moveTo(source_pos)
        
        # Add a curve to the path
        control_point1 = QPointF(source_pos.x() + (target_pos.x() - source_pos.x()) * 0.5, source_pos.y())
        control_point2 = QPointF(source_pos.x() + (target_pos.x() - source_pos.x()) * 0.5, target_pos.y())
        self._path.cubicTo(control_point1, control_point2, target_pos)
        
        # Update the path
        self.update()
        
    def boundingRect(self):
        if not self.source_node or not self.target_node:
            return QRectF()
        return self._path.boundingRect()
        
    def paint(self, painter, option, widget):
        if not self.source_node or not self.target_node:
            return
            
        # Set up the painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient
        gradient = QLinearGradient(
            self.source_node.pos(),
            self.target_node.pos()
        )
        gradient.setColorAt(0, QColor(100, 100, 100, int(255 * self._opacity)))
        gradient.setColorAt(1, QColor(100, 100, 100, int(255 * self._opacity)))
        
        # Set the pen with gradient
        pen = QPen(gradient, 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        # Draw the path
        painter.drawPath(self._path)

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

class ToolNode(QGraphicsObject):
    positionChanged = pyqtSignal()  # Add signal for position changes
    
    def __init__(self, tool_type: str):
        super().__init__()
        self.tool_type = tool_type
        self.node_id = str(uuid.uuid4())
        self.width = 120
        self.height = 60
        self.opacity = 1.0
        self.properties = {}  # Initialize properties dictionary
        
        # Set flags for interaction
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Initialize hover animation
        self.hover_animation = QPropertyAnimation(self, b"opacity")
        self.hover_animation.setDuration(150)
        self.hover_animation.setStartValue(1.0)
        self.hover_animation.setEndValue(0.7)
        
        # Set tooltip
        self.setToolTip(tool_type)
        
        # Initialize connections
        self.connections = []
        
    def get_workflow_manager(self):
        scene = self.scene()
        if scene and hasattr(scene, 'workflow_manager'):
            return scene.workflow_manager
        return None
        
    def create_connection(self, target_type: str):
        # Find target nodes of the specified type
        target_nodes = []
        for item in self.scene().items():
            if isinstance(item, ToolNode) and item.tool_type == target_type and item != self:
                target_nodes.append(item)
        
        if not target_nodes:
            QMessageBox.warning(None, "No Target", f"No {target_type} nodes found to connect to.")
            return
            
        # Create connection to the first target node
        target_node = target_nodes[0]
        
        # Check if connection already exists
        for conn in self.connections:
            if conn.target_node == target_node:
                QMessageBox.warning(None, "Connection Exists", "These nodes are already connected.")
                return
                
        # Create the connection
        connection = ConnectionLine(self, target_node)
        self.scene().addItem(connection)
        self.connections.append(connection)
        target_node.connections.append(connection)
        
        # Update workflow manager
        workflow_manager = self.get_workflow_manager()
        if workflow_manager:
            workflow_manager.add_connection(self.node_id, target_node.node_id)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu()
            
            # Add Configure action
            configure_action = menu.addAction("Configure")
            configure_action.triggered.connect(self.configure_tool)
            
            # Add Preview Data action
            preview_action = menu.addAction("Preview Data")
            preview_action.triggered.connect(self.preview_data)
            
            # Add Connect to... submenu
            connect_menu = menu.addMenu("Connect to...")
            
            # Get all nodes in the scene
            for item in self.scene().items():
                if isinstance(item, ToolNode) and item != self:
                    action = connect_menu.addAction(item.tool_type)
                    action.triggered.connect(lambda checked, t=item.tool_type: self.create_connection(t))
            
            # Add Delete action
            delete_action = menu.addAction("Delete")
            delete_action.triggered.connect(self.delete_node)
            
            menu.exec(event.screenPos())
        else:
            super().mousePressEvent(event)
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter, option, widget):
        # Draw node background
        painter.setBrush(QBrush(TOOL_COLORS.get(self.tool_type, QColor(240, 240, 240))))
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRoundedRect(0, 0, self.width, self.height, 10, 10)
        
        # Draw tool icon
        icon_path = f"icons/{self.tool_type.lower()}.svg"
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            painter.drawPixmap(10, 10, 40, 40, icon.pixmap(40, 40))
        
        # Draw tool name
        painter.setPen(QPen(QColor(50, 50, 50)))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(60, 30, self.tool_type)
        
        # Draw input/output ports
        port_radius = 5
        painter.setBrush(QBrush(QColor(100, 100, 100)))
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        
        # Input port
        painter.drawEllipse(0, int(self.height/2 - port_radius), port_radius*2, port_radius*2)
        
        # Output port
        painter.drawEllipse(self.width - port_radius*2, int(self.height/2 - port_radius), port_radius*2, port_radius*2)
        
    def configure_tool(self):
        workflow_manager = self.get_workflow_manager()
        if not workflow_manager:
            QMessageBox.critical(None, "Error", "Workflow manager not found.")
            return
            
        if self.tool_type == "Select":
            dialog = SelectToolDialog(self.properties.get('columns', []), self.scene().parent())
            if dialog.exec():
                self.properties = dialog.get_selected_fields()
                workflow_manager.update_node_properties(self.node_id, self.properties)
        elif self.tool_type == "Filter":
            dialog = FilterToolDialog(self.properties.get('columns', []), self.scene().parent())
            if dialog.exec():
                self.properties = dialog.get_filter_condition()
                workflow_manager.update_node_properties(self.node_id, self.properties)
        elif self.tool_type == "Aggregate":
            dialog = AggregateToolDialog(self.properties.get('columns', []), self.scene().parent())
            if dialog.exec():
                self.properties = dialog.get_aggregations()
                workflow_manager.update_node_properties(self.node_id, self.properties)
        elif self.tool_type == "Input":
            dialog = InputToolDialog(self.scene().parent())
            if dialog.exec():
                self.properties = dialog.get_configuration()
                workflow_manager.update_node_properties(self.node_id, self.properties)
        elif self.tool_type == "Output":
            dialog = OutputToolDialog(self.scene().parent())
            if dialog.exec():
                self.properties = dialog.get_configuration()
                workflow_manager.update_node_properties(self.node_id, self.properties)
                
    def preview_data(self):
        try:
            workflow_manager = self.get_workflow_manager()
            if not workflow_manager:
                QMessageBox.critical(None, "Error", "Workflow manager not found.")
                return
                
            data = workflow_manager.get_node_data(self.node_id)
            if data is not None:
                dialog = BrowseToolDialog(data, self.scene().parent())
                dialog.exec()
            else:
                QMessageBox.warning(None, "No Data", "No data available for this node.")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error previewing data: {str(e)}")
            
    def delete_node(self):
        # Remove all connections
        for connection in self.connections[:]:
            if connection.source_node == self:
                connection.target_node.connections.remove(connection)
            else:
                connection.source_node.connections.remove(connection)
            self.scene().removeItem(connection)
            
        # Remove from workflow manager
        workflow_manager = self.get_workflow_manager()
        if workflow_manager:
            workflow_manager.remove_node(self.node_id)
        
        # Remove from scene
        self.scene().removeItem(self)
        
    def hoverEnterEvent(self, event):
        self.hover_animation.setDirection(QPropertyAnimation.Direction.Forward)
        self.hover_animation.start()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.hover_animation.setDirection(QPropertyAnimation.Direction.Backward)
        self.hover_animation.start()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.positionChanged.emit()
        return super().itemChange(change, value)

class AggregateToolDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Aggregate Tool")
        self.setMinimumWidth(600)
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
        
        layout = QVBoxLayout()
        
        # Add header label
        header_label = QLabel("Configure Aggregations")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: black;
                padding: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Group By section
        group_by_layout = QHBoxLayout()
        self.group_by_checkbox = QCheckBox("Group By")
        self.group_by_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: black;
            }
        """)
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItems(columns)
        self.group_by_combo.setEnabled(False)
        self.group_by_combo.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 3px;
                color: black;
                font-weight: bold;
                background-color: #f8f9fa;
            }
        """)
        
        self.group_by_checkbox.stateChanged.connect(
            lambda state: self.group_by_combo.setEnabled(state == Qt.CheckState.Checked.value)
        )
        
        group_by_layout.addWidget(self.group_by_checkbox)
        group_by_layout.addWidget(self.group_by_combo)
        group_by_layout.addStretch()
        layout.addLayout(group_by_layout)
        
        # Create scroll area for fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Add fields section
        fields_label = QLabel("Select Fields to Aggregate")
        fields_label.setStyleSheet(self.label_style)
        scroll_layout.addWidget(fields_label)
        
        # Store field checkboxes and their aggregation checkboxes
        self.field_checkboxes = {}
        self.agg_checkboxes = {}
        
        # Available aggregation functions
        agg_functions = ["sum", "max", "min", "mean", "median", "count"]
        
        for column in columns:
            field_frame = QFrame()
            field_frame.setFrameStyle(QFrame.Shape.StyledPanel)
            field_layout = QVBoxLayout(field_frame)
            
            # Field checkbox
            field_checkbox = QCheckBox(column)
            field_checkbox.setStyleSheet("""
                QCheckBox {
                    font-weight: bold;
                    color: black;
                }
            """)
            field_layout.addWidget(field_checkbox)
            
            # Aggregation checkboxes
            agg_layout = QHBoxLayout()
            agg_checkboxes = {}
            for func in agg_functions:
                agg_checkbox = QCheckBox(func)
                agg_checkbox.setStyleSheet("""
                    QCheckBox {
                        color: black;
                    }
                """)
                agg_checkbox.setEnabled(False)
                agg_layout.addWidget(agg_checkbox)
                agg_checkboxes[func] = agg_checkbox
            
            # Connect field checkbox to enable/disable aggregation checkboxes
            field_checkbox.stateChanged.connect(
                lambda state, checkboxes=agg_checkboxes: self.toggle_agg_checkboxes(state, checkboxes)
            )
            
            field_layout.addLayout(agg_layout)
            scroll_layout.addWidget(field_frame)
            
            self.field_checkboxes[column] = field_checkbox
            self.agg_checkboxes[column] = agg_checkboxes
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        for btn in [ok_button, cancel_button]:
            btn.setStyleSheet(self.button_style)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
    
    def toggle_agg_checkboxes(self, state, checkboxes):
        for checkbox in checkboxes.values():
            checkbox.setEnabled(state == Qt.CheckState.Checked.value)
    
    def get_aggregations(self):
        aggregations = {}
        for column, field_checkbox in self.field_checkboxes.items():
            if field_checkbox.isChecked():
                agg_functions = []
                for func, checkbox in self.agg_checkboxes[column].items():
                    if checkbox.isChecked():
                        agg_functions.append(func)
                if agg_functions:
                    aggregations[column] = agg_functions
        
        group_by = None
        if self.group_by_checkbox.isChecked():
            group_by = self.group_by_combo.currentText()
        
        return aggregations, group_by

class WorkflowScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-10000, -10000, 20000, 20000)
        self.workflow_manager = WorkflowManager()
        self.connections = []
        
        # Add grid background
        self.grid = GridBackground()
        self.addItem(self.grid)
        
        # Add minimap
        self.minimap = MinimapView(self)
        self.addItem(self.minimap)

class MinimapView(QGraphicsItem):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.setZValue(1000)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.width = 200
        self.height = 150
        self.setPos(20, 20)
        self.is_hovered = False
        self.is_dragging = False
        self.drag_start = None
        self.view_rect = None

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        # Draw minimap background
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        # Draw scene content in minimap
        scale = min(self.width / self.scene.width(), self.height / self.scene.height())
        painter.scale(scale, scale)
        
        # Draw nodes
        for item in self.scene.items():
            if isinstance(item, ToolNode):
                painter.setPen(QPen(QColor(100, 100, 100), 1))
                painter.setBrush(QBrush(TOOL_COLORS.get(item.tool_type, QColor(245, 245, 245))))
                painter.drawRect(item.boundingRect().translated(item.pos()))

        # Draw view rectangle
        if self.view_rect:
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(QBrush(QColor(0, 120, 215, 30)))
            painter.drawRect(self.view_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.pos() - self.drag_start
            self.drag_start = event.pos()
            self.moveBy(delta.x(), delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        super().mouseReleaseEvent(event)

    def update_view_rect(self, view_rect):
        self.view_rect = view_rect
        self.update()

class WorkflowView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setAcceptDrops(True)
        
        # Zoom settings
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 2.0
        
        # Create zoom controls
        self.create_zoom_controls()

    def create_zoom_controls(self):
        # Create zoom controls widget
        zoom_widget = QWidget(self)
        zoom_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        zoom_layout = QHBoxLayout(zoom_widget)
        zoom_layout.setContentsMargins(4, 4, 4, 4)
        zoom_layout.setSpacing(4)

        # Zoom out button
        zoom_out_btn = QToolButton()
        zoom_out_btn.setIcon(QIcon("icons/zoom-out.png"))
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_out_btn.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 4px;
                border-radius: 2px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
        """)

        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(int(self.min_zoom * 100))
        self.zoom_slider.setMaximum(int(self.max_zoom * 100))
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_changed)
        self.zoom_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #e0e0e0;
                height: 4px;
                background: #f0f0f0;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #e0e0e0;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)

        # Zoom in button
        zoom_in_btn = QToolButton()
        zoom_in_btn.setIcon(QIcon("icons/zoom-in.png"))
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_in_btn.setStyleSheet(zoom_out_btn.styleSheet())

        # Add widgets to layout
        zoom_layout.addWidget(zoom_out_btn)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(zoom_in_btn)

        # Position zoom controls
        zoom_widget.setFixedSize(200, 32)
        zoom_widget.move(10, 10)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl + mouse wheel
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 0.85
            self.zoom(zoom_factor)
        else:
            super().wheelEvent(event)

    def zoom(self, factor):
        new_zoom = self.zoom_factor * factor
        if self.min_zoom <= new_zoom <= self.max_zoom:
            self.zoom_factor = new_zoom
            self.scale(factor, factor)
            self.zoom_slider.setValue(int(self.zoom_factor * 100))

    def zoom_in(self):
        self.zoom(1.15)

    def zoom_out(self):
        self.zoom(0.85)

    def zoom_slider_changed(self, value):
        factor = value / 100.0
        self.resetTransform()
        self.scale(factor, factor)
        self.zoom_factor = factor

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            tool_type = event.mimeData().text()
            print(f"Creating tool node of type: {tool_type}")
            tool_node = ToolNode(tool_type)
            print(f"Tool node created with ID: {tool_node.node_id}")
            self.scene().addItem(tool_node)
            
            # Position the node at the drop position
            drop_pos = self.mapToScene(event.position().toPoint())
            tool_node.setPos(drop_pos)
            
            # Add to workflow manager
            print(f"Adding node to workflow manager: {tool_node.node_id}")
            self.scene().workflow_manager.add_node(
                tool_node.node_id,
                tool_type,
                {'x': tool_node.pos().x(), 'y': tool_node.pos().y()},
                tool_node.properties
            )
            
            event.acceptProposedAction()

class ToolListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setDragDropMode(QListWidget.DragDropMode.DragOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item is None:
            return

        mimeData = QMimeData()
        mimeData.setText(item.text())

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(item.icon().pixmap(32, 32))
        drag.exec(Qt.DropAction.CopyAction)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Be Better ETL")
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create tools panel with styled list and icons
        tools_panel = ToolListWidget()
        tools_panel.setMaximumWidth(200)
        tools_panel.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px;
                border-radius: 6px;
                color: #333333;
                font-weight: bold;
                background-color: #f8f9fa;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #e9ecef;
                color: #333333;
            }
        """)

        # Add color-coded tool items with icons
        tools = ["Input", "Select", "Filter", "Join", "Merge", "Formula", "Output", "Browse", "Aggregate"]
        for tool in tools:
            item = QListWidgetItem(QIcon(f"icons/{tool.lower()}.png"), tool)
            color = TOOL_COLORS.get(tool, QColor(245, 245, 245))
            item.setBackground(QBrush(color))
            item.setForeground(QBrush(QColor(50, 50, 50)))
            tools_panel.addItem(item)

        layout.addWidget(tools_panel)

        # Create workflow canvas with styled view
        self.scene = WorkflowScene()
        self.view = WorkflowView(self.scene)
        self.view.setAcceptDrops(True)
        self.view.setStyleSheet("""
            QGraphicsView {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.view)

        # Connect signals
        tools_panel.itemDoubleClicked.connect(self.add_tool_to_workflow)
        
        # Update minimap when view changes
        self.view.viewport().installEventFilter(self)
        
        # Create menu bar with modern styling
        self.create_menu_bar()

    def eventFilter(self, obj, event):
        if obj == self.view.viewport() and event.type() == event.Type.Paint:
            # Update minimap view rectangle
            view_rect = self.view.mapToScene(self.view.viewport().rect()).boundingRect()
            self.scene.minimap.update_view_rect(view_rect)
        return super().eventFilter(obj, event)

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                color: #333333;
                font-weight: bold;
            }
            QMenuBar::item:selected {
                background-color: #f8f9fa;
                border-radius: 4px;
            }
            QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                color: #333333;
            }
            QMenu::item:selected {
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        
        file_menu = menubar.addMenu("File")
        
        save_action = file_menu.addAction("Save Workflow")
        save_action.triggered.connect(self.save_workflow)
        
        load_action = file_menu.addAction("Load Workflow")
        load_action.triggered.connect(self.load_workflow)
        
        run_action = file_menu.addAction("Run Workflow")
        run_action.triggered.connect(self.run_workflow)

        # Add View menu
        view_menu = menubar.addMenu("View")
        
        zoom_in_action = view_menu.addAction("Zoom In")
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.view.zoom_in)
        
        zoom_out_action = view_menu.addAction("Zoom Out")
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.view.zoom_out)
        
        reset_zoom_action = view_menu.addAction("Reset Zoom")
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(lambda: self.view.zoom_slider.setValue(100))

    def add_tool_to_workflow(self, item):
        tool_type = item.text()
        tool_node = ToolNode(tool_type)
        self.scene.addItem(tool_node)
        
        # Position the node at the center of the viewport
        view_center = self.view.mapToScene(self.view.viewport().rect().center())
        tool_node.setPos(view_center)
        
        # Add to workflow manager
        self.scene.workflow_manager.add_node(
            tool_node.node_id,
            tool_type,
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