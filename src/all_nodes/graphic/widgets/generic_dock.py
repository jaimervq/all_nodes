from PySide2 import QtWidgets, QtCore, QtGui


class GenericDock(QtWidgets.QDockWidget):
    def __init__(self, title="Dock", widget=None, parent=None):
        super().__init__(title, parent)

        self.layout().setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea
            | QtCore.Qt.RightDockWidgetArea
            | QtCore.Qt.BottomDockWidgetArea
        )

        self.widget = widget

        frame = QtWidgets.QFrame()
        frame.setObjectName("DockInnerFrame")
        frame.setStyleSheet("""
            #DockInnerFrame {
                background: #2b2b2b;

                border-left: 1px solid black;
                border-bottom: 1px solid black;

                border-top: none;
                border-right: none;

                border-bottom-left-radius: 6px;}""")

        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        layout.addWidget(self.widget)

        self.setWidget(frame)

        # Track floating state
        self.topLevelChanged.connect(self.on_top_level_changed)

    def on_top_level_changed(self, floating):
        if floating:
            self.make_window_like()
            self.move_to_cursor_screen()
        else:
            self.restore_dock_flags()

    def make_window_like(self):
        self.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowMinimizeButtonHint
            | QtCore.Qt.WindowMaximizeButtonHint
            | QtCore.Qt.WindowCloseButtonHint
        )

        self.setMinimumSize(0, 0)
        self.setMaximumSize(QtCore.QSize(16777215, 16777215))

        self.show()

    def restore_dock_flags(self):
        flags = self.windowFlags()
        flags &= ~QtCore.Qt.Window
        self.setWindowFlags(flags)
        self.show()

    def move_to_cursor_screen(self):
        pos = QtGui.QCursor.pos()
        screen = QtGui.QGuiApplication.screenAt(pos)
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.center() - self.rect().center())
