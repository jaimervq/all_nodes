__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import unittest

from all_nodes import constants
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class NodeManipulationTesting(unittest.TestCase):
    def test_add_attrs(self):
        """
        Check attributes can be added to a node instance
        """
        utils.print_test_header("test_add_attrs")

        s = LogicScene()
        n_empty = s.add_node_by_name("EmptyNode")
        n_empty.add_attribute("test_attr", constants.INPUT, int, value=100)
        self.assertEqual(n_empty["test_attr"].get_value(), 100)
        self.assertEqual(len(n_empty.get_input_attrs()), 2)
