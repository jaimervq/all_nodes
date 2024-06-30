__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore


class GlobalSignals(QtCore.QObject):
    # CLASS SCANNING ----------------------
    class_scanning_finished = QtCore.Signal()

    # WIDGET MOVE ----------------------
    class_searcher_move = QtCore.Signal(int, int)

    # TABS ----------------------
    tab_names_refresh_requested = QtCore.Signal()

    # ATTRIBUTE EDITOR ----------------------
    attribute_editor_node_addition_requested = QtCore.Signal(str)
    attribute_editor_refresh_node_requested = QtCore.Signal(str)
    attribute_editor_remove_node_requested = QtCore.Signal(str)

    attribute_editor_global_refresh_requested = QtCore.Signal()

    # CONTEXTS ----------------------
    context_expansion_requested = QtCore.Signal(str)

    # NODE CREATION ----------------------
    node_creation_requested = QtCore.Signal(QtCore.QPoint, str)

    # EXECUTION ----------------------
    execution_started = QtCore.Signal()
    execution_finished = QtCore.Signal()


class GlobalSignaler:
    # TODO should this signaler be somewhere else? It is not a widget
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(GlobalSignaler, cls).__new__(cls)
            cls.signals = GlobalSignals()
        return cls.__instance
