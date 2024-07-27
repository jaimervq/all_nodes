# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore, QtWidgets

from all_nodes import constants
from all_nodes import utils
from all_nodes.graphic.widgets.global_signaler import GlobalSignaler


GS = GlobalSignaler()

LOGGER = utils.get_logger(__name__)


BASIC_DATATYPES = sorted(
    ["bool", "dict", "float", "int", "list", "set", "str", "tuple"]
)
BASIC_DATATYPES_MAP = {
    "bool": bool,
    "dict": dict,
    "float": float,
    "int": int,
    "list": list,
    "set": set,
    "str": str,
    "tuple": tuple,
}

INPUTS_GUI = sorted([elem.value for elem in constants.InputsGUI])
INPUTS_GUI_MAP = {
    constants.InputsGUI.STR_INPUT.value: str,
    constants.InputsGUI.INT_INPUT.value: int,
    constants.InputsGUI.BOOL_INPUT.value: bool,
    constants.InputsGUI.FLOAT_INPUT.value: float,
}

OUTPUTS_GUI = sorted([elem.value for elem in constants.PreviewsGUI])
OUTPUTS_GUI_MAP = {
    constants.PreviewsGUI.STR_PREVIEW.value: str,
}


class AttributePicker(QtWidgets.QDialog):
    """TODO this description"""

    def __init__(self, *args, **kwargs):
        QtWidgets.QDialog.__init__(self, *args, **kwargs)

        self.setWindowTitle("Attribute Picker")

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.name_bar = QtWidgets.QLineEdit()
        self.name_bar.setPlaceholderText("Attribute name")
        self.layout.addWidget(self.name_bar)

        self.attribute_types_layout = QtWidgets.QHBoxLayout()

        basic_attrs_layout = QtWidgets.QVBoxLayout()
        basic_attrs_layout.addWidget(QtWidgets.QLabel("Basic types:"))
        self.basic_attrs_list = QtWidgets.QListWidget()
        self.basic_attrs_list.addItems(BASIC_DATATYPES)
        basic_attrs_layout.addWidget(self.basic_attrs_list)
        in_out_layout = QtWidgets.QHBoxLayout()
        self.in_checkbox = QtWidgets.QCheckBox(constants.INPUT)
        self.in_checkbox.setChecked(True)
        in_out_layout.addWidget(self.in_checkbox)
        self.out_checkbox = QtWidgets.QCheckBox(constants.OUTPUT)
        in_out_layout.addWidget(self.out_checkbox)
        basic_attrs_layout.addLayout(in_out_layout)
        self.attribute_types_layout.addLayout(basic_attrs_layout)

        inputs_layout = QtWidgets.QVBoxLayout()
        inputs_layout.addWidget(QtWidgets.QLabel("GUI Inputs:"))
        self.inputs_list = QtWidgets.QListWidget()
        self.inputs_list.addItems(INPUTS_GUI)
        inputs_layout.addWidget(self.inputs_list)
        self.attribute_types_layout.addLayout(inputs_layout)

        previews_layout = QtWidgets.QVBoxLayout()
        previews_layout.addWidget(QtWidgets.QLabel("GUI Previews:"))
        self.previews_list = QtWidgets.QListWidget()
        self.previews_list.addItems(OUTPUTS_GUI)
        previews_layout.addWidget(self.previews_list)
        self.attribute_types_layout.addLayout(previews_layout)

        self.layout.addLayout(self.attribute_types_layout)

        self.ok_button = QtWidgets.QPushButton("DONE")
        self.ok_button.setDisabled(True)
        self.layout.addWidget(self.ok_button)

        # Style
        f = QtCore.QFile(r"ui:stylesheet.qss")  # TODO not ideal, maybe a reduced qss?
        with open(f.fileName(), "r") as s:
            self.setStyleSheet(s.read())

        # Connections
        self.make_connections()

        self.exec_()

    def make_connections(self):
        self.name_bar.textChanged.connect(self.validate_inputs)

        self.basic_attrs_list.itemClicked.connect(self.validate_inputs)
        self.basic_attrs_list.itemClicked.connect(self.inputs_list.clearSelection)
        self.basic_attrs_list.itemClicked.connect(self.previews_list.clearSelection)

        self.inputs_list.itemClicked.connect(self.validate_inputs)
        self.inputs_list.itemClicked.connect(self.basic_attrs_list.clearSelection)
        self.inputs_list.itemClicked.connect(self.previews_list.clearSelection)

        self.previews_list.itemClicked.connect(self.validate_inputs)
        self.previews_list.itemClicked.connect(self.basic_attrs_list.clearSelection)
        self.previews_list.itemClicked.connect(self.inputs_list.clearSelection)

        self.in_checkbox.clicked.connect(self.out_checkbox.toggle)
        self.out_checkbox.clicked.connect(self.in_checkbox.toggle)

        self.ok_button.clicked.connect(self.close)

    def validate_inputs(self):
        if not self.name_bar.text():
            self.ok_button.setEnabled(False)
            return
        else:
            self.ok_button.setEnabled(True)

        if (
            not self.basic_attrs_list.selectedItems()
            and not self.inputs_list.selectedItems()
            and not self.previews_list.selectedItems()
        ):
            self.ok_button.setEnabled(False)

    def get_results(self):
        name = self.name_bar.text()

        if self.basic_attrs_list.selectedItems():
            attr_type = self.basic_attrs_list.currentItem().text()
            attr_connector = (
                constants.INPUT if self.in_checkbox.isChecked() else constants.OUTPUT
            )

            return [name, attr_connector, BASIC_DATATYPES_MAP.get(attr_type)]

        elif self.inputs_list.selectedItems():
            if not name.startswith("internal_"):
                name = "internal_" + name
            gui_type = self.inputs_list.currentItem().text()
            return [
                name,
                constants.INTERNAL,
                INPUTS_GUI_MAP.get(gui_type),
                constants.InputsGUI(gui_type),
            ]

        elif self.previews_list.selectedItems():
            if not name.startswith("internal_"):
                name = "internal_" + name
            gui_type = self.previews_list.currentItem().text()
            return [
                name,
                constants.INTERNAL,
                OUTPUTS_GUI_MAP.get(gui_type),
                constants.PreviewsGUI(gui_type),
            ]
