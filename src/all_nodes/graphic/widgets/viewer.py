import ctypes
import math

import numpy as np
import PyOpenColorIO as ocio
from PySide2 import QtWidgets, QtCore, QtGui

from all_nodes import constants
from all_nodes.logic.global_signaler import GLOBAL_SIGNALER as GS


class ViewerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.viewingNode = None
        self.ocio_config = ocio.Config.CreateFromFile(
            QtCore.QFile(r"ui:config.ocio").fileName()
        )
        self.build_ui()

        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        self.setStyleSheet("""
        QGraphicsView  {
            background-color: rgb(128, 128, 128);
            border-radius: 8px;
        }
        """)

        self.make_connections()

    def make_connections(self):
        self.attribute_combo.currentTextChanged.connect(self.display_attribute)

        self.view.mouse_moved.connect(self.on_mouse_moved)

        self.display_combo.currentTextChanged.connect(self.populate_views)
        self.blend_checkbox.toggled.connect(self.on_blend_toggle)
        self.gamma_slider.valueChanged.connect(self.on_gamma_slider)
        self.gamma_spin.valueChanged.connect(self.on_gamma_spin)

        GS.signals.execution_finished.connect(self.display_current_attribute)
        GS.signals.workspace_cleared.connect(self.reset)

    def on_mouse_moved(self, pos):
        self.x_label.setText(f"X:  {math.ceil(pos.x())}")
        self.y_label.setText(f"Y:  {math.ceil(pos.y())}")

    def on_blend_toggle(self, state):
        self.gl.blend_enabled = state
        self.gl.update()

    def on_gamma_slider(self, v):
        g = v / 100.0

        self.gamma_spin.blockSignals(True)
        self.gamma_spin.setValue(g)
        self.gamma_spin.blockSignals(False)

        self.gl.global_gamma = g
        self.gl.update()

    def on_gamma_spin(self, g):
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(int(g * 100))
        self.gamma_slider.blockSignals(False)

        self.gl.global_gamma = g
        self.gl.update()

    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # ------------------ TOP BAR
        self.top_bar = QtWidgets.QWidget()
        self.top_bar.setFixedHeight(32)

        bar_layout = QtWidgets.QHBoxLayout(self.top_bar)
        bar_layout.setContentsMargins(6, 2, 6, 2)
        bar_layout.setSpacing(2)

        # Attribute dropdown
        self.node_name_label = QtWidgets.QLabel("[node].")
        self.node_name_label.setFont(QtGui.QFont("arial", 12))
        bar_layout.addWidget(self.node_name_label)
        self.attribute_combo = QtWidgets.QComboBox()
        self.attribute_combo.setFont(self.node_name_label.font())
        self.attribute_combo.setMinimumWidth(150)
        self.attribute_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        bar_layout.addWidget(self.attribute_combo)
        bar_layout.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding)
        )

        main_layout.addWidget(self.top_bar)

        # ------------------ 2D VIEWER
        self.hybrid_2d_viewer_container = QtWidgets.QWidget()
        self.hybrid_2d_viewer_container_layout = QtWidgets.QVBoxLayout()
        self.hybrid_2d_viewer_container_layout.setContentsMargins(0, 0, 0, 0)
        self.hybrid_2d_viewer_container.setLayout(
            self.hybrid_2d_viewer_container_layout
        )

        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setSceneRect(-10000, -10000, 20000, 20000)
        self.view = ViewerGraphicsView(self.scene, parent=self)
        self.view.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform
        )
        self.view.setAlignment(QtCore.Qt.AlignCenter)

        camera = Camera()
        self.view.set_camera(camera)
        self.gl = GLImageViewer(camera, overlay_view=self.view, parent=self)

        self.hybrid_2d_viewer = Hybrid2dViewer(self.view, self.gl, parent=self)
        self.hybrid_2d_viewer_container_layout.addWidget(self.hybrid_2d_viewer)

        # --- Bar colorspaces
        self.bar_colorspaces = QtWidgets.QWidget()
        self.bar_colorspaces.setFixedHeight(32)

        bar_layout_colorspaces = QtWidgets.QHBoxLayout(self.bar_colorspaces)
        bar_layout_colorspaces.setContentsMargins(6, 2, 6, 2)
        bar_layout_colorspaces.setSpacing(10)

        # Display dropdown
        font_colorspaces = QtGui.QFont("arial", 9)
        self.display_combo = QtWidgets.QComboBox()
        self.display_combo.setFont(font_colorspaces)
        lbl = QtWidgets.QLabel("Display:")
        lbl.setFont(font_colorspaces)
        bar_layout_colorspaces.addWidget(lbl)
        bar_layout_colorspaces.addWidget(self.display_combo)

        # View dropdown
        self.view_combo = QtWidgets.QComboBox()
        self.view_combo.setFont(font_colorspaces)
        lbl = QtWidgets.QLabel("View:")
        lbl.setFont(font_colorspaces)
        bar_layout_colorspaces.addWidget(lbl)
        bar_layout_colorspaces.addWidget(self.view_combo)
        bar_layout_colorspaces.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding)
        )

        self.populate_displays()
        if self.display_combo.count():
            self.populate_views(self.display_combo.currentText())

        # self.hybrid_2d_viewer_container_layout.addWidget(self.bar_colorspaces) TODO colorspaces

        # --- Info bar
        self.info_bar = QtWidgets.QWidget(parent=self.hybrid_2d_viewer)
        self.info_bar.setStyleSheet("background:transparent;")
        self.info_bar.setFixedHeight(32)
        self.info_bar.setMinimumWidth(400)

        info_layout = QtWidgets.QHBoxLayout(self.info_bar)
        info_layout.setContentsMargins(6, 2, 6, 2)
        info_layout.setSpacing(8)

        info_layout.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding)
        )
        self.x_label = QtWidgets.QLabel("X")
        self.x_label.setStyleSheet(
            "background-color:rgba(0,0,0,210); color:red; border-radius:4px"
        )
        self.x_label.setFont(QtGui.QFont("arial", 9))
        self.x_label.setAlignment(QtCore.Qt.AlignCenter)
        self.x_label.setFixedWidth(100)
        info_layout.addWidget(self.x_label)
        self.y_label = QtWidgets.QLabel("Y")
        self.y_label.setStyleSheet(
            "background-color:rgba(0,0,0,210); color:green; border-radius:4px"
        )
        self.y_label.setFont(QtGui.QFont("arial", 9))
        self.y_label.setAlignment(QtCore.Qt.AlignCenter)
        self.y_label.setFixedWidth(100)
        info_layout.addWidget(self.y_label)

        # --- Blend controls
        self.blend_bar = QtWidgets.QWidget()
        blend_layout = QtWidgets.QHBoxLayout(self.blend_bar)
        blend_layout.setContentsMargins(6, 2, 6, 2)

        self.blend_checkbox = QtWidgets.QCheckBox("Blend")
        self.blend_checkbox.setChecked(False)

        self.gamma_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.gamma_slider.setRange(1, 400)
        self.gamma_slider.setValue(100)
        self.gamma_slider.setFixedWidth(120)

        self.gamma_spin = QtWidgets.QDoubleSpinBox()
        self.gamma_spin.setRange(0.01, 4.0)
        self.gamma_spin.setSingleStep(0.01)
        self.gamma_spin.setDecimals(2)
        self.gamma_spin.setValue(1.0)
        self.gamma_spin.setFixedWidth(70)

        blend_layout.addWidget(self.blend_checkbox)
        blend_layout.addWidget(QtWidgets.QLabel("Gamma"))
        blend_layout.addWidget(self.gamma_slider)
        blend_layout.addWidget(self.gamma_spin)
        blend_layout.addSpacerItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding)
        )

        self.hybrid_2d_viewer_container_layout.addWidget(self.blend_bar)
        main_layout.addWidget(self.hybrid_2d_viewer_container)

        # ------------------ DATA VIEWER
        self.data_viewer = QtWidgets.QTableView()
        self.data_viewer.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )
        self.data_viewer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.data_model = PolarsModel()
        self.data_viewer.setModel(self.data_model)
        self.data_viewer.setSortingEnabled(True)
        self.data_viewer.resizeColumnsToContents()
        main_layout.addWidget(self.data_viewer)

        # ------------------ CONNECTIONS
        self.make_connections()

        # ------------------ UPDATE
        self.re_layout()

    def populate_displays(self):
        self.display_combo.clear()

        displays = self.ocio_config.getDisplays()
        for d in displays:
            self.display_combo.addItem(d)

    def populate_views(self, display):
        self.view_combo.clear()

        views = self.ocio_config.getViews(display)
        for v in views:
            self.view_combo.addItem(v)

    def set_node(self, node):
        self.clear_all_viewers()

        self.viewingNode = node
        self.repopulate_attributes()
        self.display_current_attribute()

    def re_layout(self):
        self.info_bar.setFixedWidth(self.hybrid_2d_viewer.width() - 8)
        self.info_bar.move(
            0,
            self.view.pos().y()
            + self.hybrid_2d_viewer.height()
            - self.info_bar.height()
            - 20,
        )

    def resizeEvent(self, event):
        self.re_layout()
        self.display_current_attribute()
        return super().resizeEvent(event)

    def set_node_name_label(self):
        self.node_name_label.clear()
        if not self.viewingNode:
            self.node_name_label.setText("[node].")
            return
        text = f"{self.viewingNode.full_name}."
        self.node_name_label.setText(text)

    def repopulate_attributes(self):
        """Populate attribute dropdown"""
        self.attribute_combo.clear()
        attrs_to_view = (
            self.viewingNode.get_output_attrs() + self.viewingNode.get_input_attrs()
        )
        attrs_to_view += [
            self.viewingNode[attr_name]
            for attr_name in self.viewingNode.get_gui_internals_previews().keys()
        ]
        if not attrs_to_view:
            return
        attrs_to_view.sort(key=lambda a: a.attribute_name)
        for attr in attrs_to_view:
            if attr.attribute_name in [constants.START, constants.COMPLETED]:
                continue
            self.attribute_combo.addItem(attr.attribute_name)

        self.attribute_combo.setEnabled(bool(self.attribute_combo.count()))
        self.attribute_combo.adjustSize()

    def display_current_attribute(self):
        self.display_attribute(self.attribute_combo.currentText())

    def hide_all_viewers(self):
        for viewer in [self.hybrid_2d_viewer_container, self.data_viewer]:
            viewer.hide()

    def display_attribute(self, attr_name):
        # Check name of the attribute to view
        self.set_node_name_label()
        if not attr_name:
            return

        # Hide all viewers
        self.hide_all_viewers()

        # Clear everything in viewers
        self.clear_all_viewers()

        # Managing images
        if self.viewingNode[attr_name].get_datatype_str() == "Image":
            self.hybrid_2d_viewer_container.show()
            image = self.viewingNode.get_attribute_value(attr_name)
            if image is None:
                text_item = self.scene.addText("No image")
                text_item.setDefaultTextColor(QtGui.QColor(255, 255, 255, 80))
                self.view.fit_scene()
                return
            self.hybrid_2d_viewer.set_pil_image(image)
            return

        elif self.viewingNode[attr_name].get_datatype_str() == "RustImage":
            self.hybrid_2d_viewer_container.show()
            image = self.viewingNode.get_attribute_value(attr_name)
            if image is None:
                text_item = self.scene.addText("No image")
                text_item.setDefaultTextColor(QtGui.QColor(255, 255, 255, 80))
                self.view.fit_scene()
                return
            self.hybrid_2d_viewer.set_rust_image(image)
            return

        elif self.viewingNode[attr_name].get_datatype_str() == "DataFrame":
            self.data_viewer.show()
            dataframe = self.viewingNode.get_attribute_value(attr_name)
            self.data_model.set_df(dataframe)

        # Else, display text
        else:
            self.hybrid_2d_viewer_container.show()
            value = self.viewingNode.get_attribute_value_as_string(attr_name)
            item = QtWidgets.QGraphicsTextItem()
            item.setDefaultTextColor(QtGui.QColor(255, 255, 255, 255))
            item.setHtml(value)
            self.scene.addItem(item)
            item.setPos(0, 0)
            if value == "True":
                item.setDefaultTextColor(QtGui.QColor("cyan"))
            elif value == "False":
                item.setDefaultTextColor(QtGui.QColor("magenta"))
            elif value == "None":
                item.setDefaultTextColor(QtGui.QColor(255, 255, 255, 80))

        self.view.fit_scene()

    def clear_all_viewers(self):
        self.hybrid_2d_viewer.clear()
        self.data_viewer.model().clear()

    def reset(self):
        self.node_name_label.setText("[node].")
        self.attribute_combo.clear()
        self.set_node(None)

        self.hide_all_viewers()

    def showEvent(self, event):
        super().showEvent(event)
        self.re_layout()
        self.display_current_attribute()


class ViewerGraphicsView(QtWidgets.QGraphicsView):
    mouse_moved = QtCore.Signal(QtCore.QPointF)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        # CAMERA ----------------------
        self.camera = None
        self._zoom = 0
        self._zoom_step = 1.15
        self._zoom_range = (-20, 50)

        # CAMERA PANNING ----------------------
        self._panning = False
        self._pan_start = QtCore.QPoint()

        # BB ----------------------
        self._bb = None

        # RENDERING ----------------------
        self.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform
        )
        self.setStyleSheet("background: transparent")
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.viewport().setAutoFillBackground(False)
        self.viewport().setStyleSheet("background: transparent")

        # SCROLLING, TRANSFORMATIONS ----------------------
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)

        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)

        # ALIGNMENT ----------------------
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        # INIT ----------------------
        rect = QtCore.QRectF(-20, -20, 200, 200)
        self.resetTransform()
        self.fitInView(rect, QtCore.Qt.KeepAspectRatio)

    def set_camera(self, camera):
        self.camera = camera
        self.camera.changed.connect(self.apply_camera)

    def apply_camera(self):
        t = QtGui.QTransform()
        t.scale(self.camera.scale, self.camera.scale)
        t.translate(self.camera.offset.x(), self.camera.offset.y())
        self.setTransform(t)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.save()

        # Setup ------
        grid_pen = QtGui.QPen(QtGui.QColor(100, 100, 100, 180))
        grid_pen.setWidth(0)  # cosmetic pen
        painter.setPen(grid_pen)

        font = painter.font()
        font.setPointSize(1)
        painter.setFont(font)
        text_pen = QtGui.QPen(QtGui.QColor(220, 220, 220))

        #  Axes, grid lines and numbers ------
        step = 10
        x_start = int(rect.left() // step) * step
        x_end = int(rect.right() // step + 1) * step
        y_start = int(rect.top() // step) * step
        y_end = int(rect.bottom() // step + 1) * step

        # Axes
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0, 255), 0))  # X axis
        painter.drawLine(rect.left(), 0, rect.right(), 0)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0, 255), 0))  # Y axis
        painter.drawLine(0, rect.top(), 0, rect.bottom())

        # Vertical lines
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 200), 0))
        for x in range(x_start, x_end, step):
            if x == 0:
                continue
            painter.drawLine(x, 0, x, -3)

        # Horizontal lines
        for y in range(y_start, y_end, step):
            if y == 0:
                continue
            painter.drawLine(-3, y, 0, y)

        # Numbers next to axes in scene
        painter.setPen(text_pen)

        for y in range(y_start, y_end, step):
            if y == 0:
                continue
            self.draw_axis_label(
                painter, QtCore.QPointF(0, y), str(y), axis="y", side="left"
            )

        for x in range(x_start, x_end, step):
            if x == 0:
                continue
            self.draw_axis_label(
                painter, QtCore.QPointF(x, 0), str(x), axis="x", side="top"
            )

        # BB
        if self._bb is not None:
            painter.setFont(QtGui.QFont("arial", max(self._bb[0] * 0.02, 2)))
            painter.drawText(
                max(self._bb[0] + 3, self._bb[0] * 1.005),
                max(self._bb[1] + 3, self._bb[1] * 1.005),
                1e6,
                1e6,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop,
                "w: " + str(self._bb[0]) + " x  h: " + str(self._bb[1]),
            )
            painter.setPen(
                QtGui.QPen(QtGui.QColor(255, 255, 255, 255), 0, QtCore.Qt.DashLine)
            )
            extend = max(self._bb[0] * 0.15, self._bb[1] * 0.15)
            painter.drawLine(self._bb[0], 0, self._bb[0], self._bb[1] + extend)
            painter.drawLine(0, self._bb[1], self._bb[0] + extend, self._bb[1])

        painter.restore()

    def clear(self):
        self.scene().clear()
        self._bb = None

    def draw_axis_label(self, painter, pos, text, axis="y", side="left", margin=4):
        original_font = painter.font()

        if (
            int(pos.y())
            and int(pos.y()) % 100 == 0
            or int(pos.x())
            and int(pos.x()) % 100 == 0
        ):
            painter.setFont(
                QtGui.QFont(painter.font().family(), painter.font().pointSize() + 1.6)
            )

        fm = QtGui.QFontMetrics(original_font)
        w = fm.horizontalAdvance(text) * 2.5
        h = fm.height() * 2.5

        if axis == "y":
            if side == "left":
                rect = QtCore.QRectF(pos.x() - w - margin, pos.y() - h / 2, w, h)
                align = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            else:
                rect = QtCore.QRectF(pos.x() + margin, pos.y() - h / 2, w, h)
                align = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter

        else:  # axis == "x"
            if side == "top":
                rect = QtCore.QRectF(pos.x() - w / 2, pos.y() - h - margin, w, h)
                align = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom
            else:
                rect = QtCore.QRectF(pos.x() - w / 2, pos.y() + margin, w, h)
                align = QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop

        painter.drawText(rect, align, text)

        painter.setFont(original_font)

    def add_indicator(self, w, h):
        self._bb = (w, h)
        self.update()

    def sync_camera_from_view(self):
        t = self.viewportTransform()

        self.camera.scale = t.m11()
        self.camera.offset = QtCore.QPointF(t.m31(), t.m32())

        self.camera.changed.emit()

    def fit_scene(self):
        rect = self.scene().itemsBoundingRect() + QtCore.QMarginsF(10, 10, 10, 10)
        if rect.isNull():
            return

        self._zoom = 0
        self.resetTransform()
        self.fitInView(rect, QtCore.Qt.KeepAspectRatio)
        self.sync_camera_from_view()

    def wheelEvent(self, event):
        if event.angleDelta().y() == 0:
            return

        factor = self._zoom_step if event.angleDelta().y() > 0 else 1 / self._zoom_step

        old_pos = self.mapToScene(event.pos())

        self.camera.scale *= factor

        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos

        self.camera.offset += delta
        self.camera.changed.emit()

        event.accept()

    def mouseMoveEvent(self, event):
        if self._panning:
            old = self.mapToScene(self._pan_start)
            new = self.mapToScene(event.pos())
            delta = new - old

            self._pan_start = event.pos()

            self.camera.offset += delta
            self.camera.changed.emit()

        scene_pos = self.mapToScene(event.pos())
        self.mouse_moved.emit(scene_pos)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._panning = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if (
            event.modifiers() == QtCore.Qt.ControlModifier
            and event.key() == QtCore.Qt.Key_0
        ):
            self.fit_scene()
            return

        super().keyPressEvent(event)


class Camera(QtCore.QObject):
    changed = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.scale = 1.0
        self.offset = QtCore.QPointF(0, 0)

    def zoom(self, factor):
        self.scale *= factor
        self.changed.emit()

    def pan(self, delta):
        self.offset += delta
        self.changed.emit()

    def get_matrix(self, view):
        t = view.viewportTransform()

        sx = t.m11()
        sy = t.m22()
        tx = t.m31() - view.viewport().width() / 2
        ty = t.m32() - view.viewport().height() / 2

        return [sx, 0.0, 0.0, 0.0, sy, 0.0, tx, ty, 1.0]

    def get_projection(self, w, h):
        fac = 2.0
        sx = fac / w
        sy = -fac / h

        return [sx, 0.0, 0.0, 0.0, sy, 0.0, 0.0, 0.0, 1.0]


class GLImageViewer(QtWidgets.QOpenGLWidget):
    def __init__(self, camera, overlay_view, parent=None):
        super().__init__(parent)

        self.overlay_view = overlay_view

        self._clear_requested = False

        self.zoom = 1.0
        self.camera = camera
        self.camera.changed.connect(self.update)

        self.blend_enabled = False
        self.global_gamma = 1.0

        self.pending_pil_image = None
        self.pending_rust_image = None
        self.tex = None
        self.img_h = 0
        self.img_w = 0

        # transparency
        self.setAutoFillBackground(False)

        self.setMouseTracking(True)

        self.camera.changed.connect(self.request_render)

    def request_render(self):
        self.update()

    def event(self, e):
        if e.type() in (
            QtCore.QEvent.WindowChangeInternal,
            QtCore.QEvent.ParentChange,
            QtCore.QEvent.Show,
            QtCore.QEvent.Hide,
        ):
            QtCore.QTimer.singleShot(0, self.update)

        return super().event(e)

    def clear_up_gl(self):
        from OpenGL import GL

        if not self.context() or not self.context().isValid():
            return

        self.makeCurrent()

        if getattr(self, "tex", None):
            GL.glDeleteTextures([self.tex])
            self.tex = None

        if getattr(self, "vbo", None):
            GL.glDeleteBuffers(1, [self.vbo])
            self.vbo = None

        if getattr(self, "program", None):
            GL.glDeleteProgram(self.program)
            self.program = None

        self.doneCurrent()

    # -------------------------
    # OpenGL init
    # -------------------------
    def initializeGL(self):
        self.context().aboutToBeDestroyed.connect(self.clear_up_gl)
        from OpenGL import GL

        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        # ---- shaders ----
        vs = """
            #version 330

            in vec3 position;
            in vec2 uv;

            out vec2 v_uv;

            uniform mat3 camera;
            uniform mat3 projection;

            void main()
            {
                vec3 p = vec3(position.xy, 1.0);
                p = camera * p;
                p = projection * p;

                v_uv = uv;
                gl_Position = vec4(p.xy, 0.0, 1.0);
            }
        """

        fs = """
            #version 330

            in vec2 v_uv;
            out vec4 color;

            uniform sampler2D tex;
            uniform float gamma;

            void main()
            {
                vec4 c = texture(tex, v_uv);

                c.rgb = max(c.rgb, vec3(0.0));
                c.rgb = pow(c.rgb, vec3(1.0 / gamma));

                color = c;
            }
        """

        self.program = GL.glCreateProgram()

        v = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(v, vs)
        GL.glCompileShader(v)

        f = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(f, fs)

        GL.glCompileShader(f)

        GL.glAttachShader(self.program, v)
        GL.glAttachShader(self.program, f)
        GL.glLinkProgram(self.program)

        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, 0, None, GL.GL_DYNAMIC_DRAW)

    # -------------------------
    # draw
    # -------------------------
    def paintGL(self):
        from OpenGL import GL

        ctx = self.context()
        if not ctx or not ctx.isValid():
            return

        if self.pending_pil_image is not None:
            self.load_pil_image(self.pending_pil_image)
            self.pending_pil_image = None

        elif self.pending_rust_image is not None:
            self.load_rust_exr_zero_copy(self.pending_rust_image)
            self.pending_rust_image = None

        GL.glClearColor(0.5, 0.5, 0.5, 0)

        from OpenGL import GL

        if self.blend_enabled:
            GL.glEnable(GL.GL_BLEND)
        else:
            GL.glDisable(GL.GL_BLEND)

        if not hasattr(self, "program"):
            return

        if self.tex is None:
            return

        GL.glUseProgram(self.program)

        gamma_loc = GL.glGetUniformLocation(self.program, "gamma")
        GL.glUniform1f(gamma_loc, self.global_gamma)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)

        pos_loc = GL.glGetAttribLocation(self.program, "position")
        uv_loc = GL.glGetAttribLocation(self.program, "uv")

        stride = 5 * 4  # 5 floats

        GL.glEnableVertexAttribArray(pos_loc)
        GL.glVertexAttribPointer(
            pos_loc, 3, GL.GL_FLOAT, False, stride, ctypes.c_void_p(0)
        )

        GL.glEnableVertexAttribArray(uv_loc)
        GL.glVertexAttribPointer(
            uv_loc, 2, GL.GL_FLOAT, False, stride, ctypes.c_void_p(12)
        )
        cam_loc = GL.glGetUniformLocation(self.program, "camera")
        proj_loc = GL.glGetUniformLocation(self.program, "projection")

        proj = np.array(
            self.camera.get_projection(self.width(), self.height()), dtype=np.float32
        )

        cam = np.array(self.camera.get_matrix(self.overlay_view), dtype=np.float32)

        GL.glUniformMatrix3fv(proj_loc, 1, False, proj)
        GL.glUniformMatrix3fv(cam_loc, 1, False, cam)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)
        GL.glUniform1i(GL.glGetUniformLocation(self.program, "tex"), 0)

        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    def load_pil_image(self, pil_img):
        from OpenGL import GL

        pil_img = pil_img.convert("RGBA")
        self.img_w, self.img_h = pil_img.size
        data = pil_img.tobytes()

        vertices = np.array(
            [
                [0, 0, 0, 0, 0],
                [self.img_w, 0, 0, 1, 0],
                [0, self.img_h, 0, 0, 1],
                [self.img_w, self.img_h, 0, 1, 1],
            ],
            dtype="float32",
        )

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW
        )

        if self.tex is None:
            self.tex = GL.glGenTextures(1)

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)

        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA,
            self.img_w,
            self.img_h,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            data,
        )

        # viewer-friendly filtering
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        self.update()

    def load_rust_exr_zero_copy(self, rust_img):
        from OpenGL import GL

        # ----- size -----
        self.img_w = rust_img.width
        self.img_h = rust_img.height

        # ----- zero-copy buffer view over Rust memory
        raw = rust_img.pixels_as_bytes()  # PyBytes referencing Rust Vec memory

        # ----- quad -----
        vertices = np.array(
            [
                [0, 0, 0, 0, 0],
                [self.img_w, 0, 0, 1, 0],
                [0, self.img_h, 0, 0, 1],
                [self.img_w, self.img_h, 0, 1, 1],
            ],
            dtype=np.float32,
        )

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW
        )

        # ----- texture -----
        if self.tex is None:
            self.tex = GL.glGenTextures(1)

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.tex)

        # Important for float RGBA EXR
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA32F,  # HDR internal format
            self.img_w,
            self.img_h,
            0,
            GL.GL_RGBA,
            GL.GL_FLOAT,
            raw,  # ⭐ direct Rust memory
        )

        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        self.update()

    def clear(self):
        if self.context() and self.context().isValid():
            self.makeCurrent()
            if self.tex is not None:
                from OpenGL import GL

                GL.glDeleteTextures([self.tex])
                self.tex = None
            self.doneCurrent()
        else:
            self.tex = None
        self.update()

    def resizeGL(self, w, h):
        QtCore.QTimer.singleShot(0, self.update)


class Hybrid2dViewer(QtWidgets.QWidget):
    def __init__(self, overlay_view, gl, parent=None):
        super().__init__()

        self.overlay = overlay_view
        self.gl = gl

        # stack layout
        stack = QtWidgets.QStackedLayout(self)
        stack.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        stack.addWidget(self.overlay)
        stack.addWidget(self.gl)

    # -------- sync overlay camera --------
    def sync_overlay(self):
        transform = QtGui.QTransform()
        transform.scale(self.camera.scale, self.camera.scale)
        self.overlay.setTransform(transform)

    def set_pil_image(self, pil_img):
        self.gl.pending_pil_image = pil_img
        self.gl.update()

        w, h = pil_img.size
        self.overlay.fitInView(
            QtCore.QRectF(0, 0, w, h) + QtCore.QMarginsF(50, 50, 50, 50),
            QtCore.Qt.KeepAspectRatio,
        )
        self.overlay.add_indicator(w, h)
        self.overlay.sync_camera_from_view()

    def set_rust_image(self, rust_img):
        self.gl.pending_rust_image = rust_img
        self.gl.update()

        w, h = rust_img.width, rust_img.height
        self.overlay.fitInView(
            QtCore.QRectF(0, 0, w, h) + QtCore.QMarginsF(50, 50, 50, 50),
            QtCore.Qt.KeepAspectRatio,
        )
        self.overlay.add_indicator(w, h)
        self.overlay.sync_camera_from_view()

    def clear(self):
        self.gl.clear()
        self.overlay.clear()

    def resizeEvent(self, event):
        return super().resizeEvent(event)


class PolarsModel(QtCore.QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._df = None

    def set_df(self, df):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def clear(self):
        self.beginResetModel()
        self._df = None
        self.endResetModel()

    def rowCount(self, parent=None):
        if self._df is None:
            return 0
        return self._df.height

    def columnCount(self, parent=None):
        if self._df is None:
            return 0
        return self._df.width

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if self._df is None:
            return None

        if not index.isValid():
            return None

        if role == QtCore.Qt.DisplayRole:
            val = self._df[index.row(), index.column()]
            return str(val)

        return None

    def headerData(self, section, orientation, role):
        if self._df is None:
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            return self._df.columns[section]
        else:
            return str(section)

    def sort(self, column, order):
        if self._df is None:
            return

        col_name = self._df.columns[column]

        self.layoutAboutToBeChanged.emit()

        reverse = order == QtCore.Qt.DescendingOrder
        self._df = self._df.sort(col_name, descending=reverse)
        self._cols = self._df.get_columns()

        self.layoutChanged.emit()
