__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore


class GlobalSignaler(QtCore.QObject):
    _instance = None

    # TABS ----------------------
    tab_names_refresh_requested = QtCore.Signal()

    # NODE-SPECIFIC ----------------------
    attribute_editor_node_addition_requested = QtCore.Signal(str)
    attribute_editor_refresh_node_requested = QtCore.Signal(str)
    attribute_editor_remove_node_requested = QtCore.Signal(str)

    # CONTEXTS ----------------------
    context_expansion_requested = QtCore.Signal(str)

    # GLOBAL REFRESH ----------------------
    attribute_editor_global_refresh_requested = QtCore.Signal()

    # EXECUTION ----------------------
    execution_started = QtCore.Signal()
    execution_finished = QtCore.Signal()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalSignaler, cls).__new__(cls)
        return cls._instance


GLOBAL_SIGNALER = GlobalSignaler()
