from PySide2 import QtCore


class GlobalSignaler(QtCore.QObject):
    _instance = None

    attribute_editor_node_addition_requested = QtCore.Signal(str)
    attribute_editor_refresh_node_requested = QtCore.Signal(str)
    attribute_editor_remove_node_requested = QtCore.Signal(str)

    attribute_editor_global_refresh_requested = QtCore.Signal()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalSignaler, cls).__new__(cls)
        return cls._instance


GLOBAL_SIGNALER = GlobalSignaler()
