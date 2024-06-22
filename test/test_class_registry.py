__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import unittest

from all_nodes.logic.class_registry import CLASS_REGISTRY as CR
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class ClassRegistryTest(unittest.TestCase):
    def test_class_registry(self):
        """
        Basic test of the class registry
        """
        utils.print_test_header("test_class_registry")

        CR.flush()
        assert CR._all_classes is None
        CR.get_all_classes()
        assert len(CR._all_classes.keys()) > 0

        CR.flush()
        assert CR._all_classes is None

    def test_class_registry_scene(self):
        """
        Test that the class registry scanning is launched when adding nodes to a scene
        """
        utils.print_test_header("test_class_registry_scene")

        CR.flush()
        assert CR._all_classes is None

        logic_scene = LogicScene()
        logic_scene.add_node_by_name("JsonToDict")

        assert len(CR._all_classes.keys()) > 2
        assert len(CR._all_classes.keys()) < 50

        CR.flush()
        assert CR._all_classes is None
