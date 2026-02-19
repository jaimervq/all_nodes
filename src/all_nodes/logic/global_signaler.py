__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from PySide2 import QtCore


class GlobalSignals(QtCore.QObject):
    # -------------------------- LOGIC -------------------------- #
    class_scanning_finished = QtCore.Signal()

    # -------------------------- WIDGETS -------------------------- #
    # Main window ----------------------
    tab_names_refresh_requested = QtCore.Signal()
    main_screen_feedback = QtCore.Signal(str, int)
    workspace_cleared = QtCore.Signal()

    # Class search ----------------------
    class_searcher_move = QtCore.Signal(int, int)

    # Attribute editor ----------------------
    attribute_editor_node_addition_requested = QtCore.Signal(str)
    attribute_editor_refresh_node_requested = QtCore.Signal(str)
    attribute_editor_remove_node_requested = QtCore.Signal(str)
    attribute_editor_global_refresh_requested = QtCore.Signal()

    # Viewer ----------------------
    viewer_refresh_requested = QtCore.Signal()
    viewer_node_changed = QtCore.Signal(str)

    # Contexts ----------------------
    context_expansion_requested = QtCore.Signal(str)

    # Node creation ----------------------
    dropped_node = QtCore.Signal()
    node_creation_requested_from_searcher = QtCore.Signal(str, QtCore.QPoint)

    # -------------------------- EXECUTION -------------------------- #
    execution_started = QtCore.Signal()
    execution_finished = QtCore.Signal()


class GlobalSignaler:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(GlobalSignaler, cls).__new__(cls)
            cls.signals = GlobalSignals()
        return cls.__instance


GLOBAL_SIGNALER = GlobalSignaler()
