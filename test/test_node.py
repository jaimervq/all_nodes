__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os
from pprint import pprint
import tempfile
import unittest

from all_nodes import constants
from all_nodes.lib.base_node_lib.nodes_general_library import debug_nodes
from all_nodes.lib.base_node_lib.nodes_general_library import file_reading_nodes
from all_nodes.lib.base_node_lib.nodes_general_library import file_writing_nodes
from all_nodes.lib.base_node_lib.nodes_general_library import folder_management_nodes
from all_nodes.lib.base_node_lib.nodes_general_library import general_nodes
from all_nodes.lib.base_node_lib.nodes_general_library import general_input_nodes
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class NodeTesting(unittest.TestCase):
    DICT_EXAMPLE = {
        "test_people": {"names": ["Fred", "Joe", "Sally"], "surnames": None}
    }

    def test_creation(self):
        """
        Create a few nodes, directly from their modules.
        """
        utils.print_test_header("test_creation")

        n_1 = debug_nodes.EmptyNode()
        self.assertIsNotNone(n_1)
        n_2 = general_nodes.GetDictKey()
        self.assertIsNotNone(n_2)
        n_3 = folder_management_nodes.CopyFoldersRecursive()
        self.assertIsNotNone(n_3)

    def test_attribute_name(self):
        """
        Test the attributes of a node get created with a proper name.
        """
        utils.print_test_header("test_attribute_name")

        n_1 = general_nodes.GetDictKey()
        in_dict_attr = n_1["in_dict"]
        self.assertRegex(in_dict_attr.dot_name, "GetDictKey_\d+\.in_dict")

    def test_connection(self):
        """
        Test connecting some node attributes.
        """
        utils.print_test_header("test_connection")

        n_1 = file_reading_nodes.JsonToDict()
        n_2 = general_nodes.GetDictKey()
        self.assertTrue(n_1.connect_attribute("out_dict", n_2, "in_dict")[0])
        self.assertFalse(n_1["out_dict"].connect_to_other(n_2["key"])[0])
        self.assertFalse(n_2["in_dict"].connect_to_other(n_2["key"])[0])
        self.assertFalse(n_2["key"].connect_to_other(n_1["out_dict"])[0])

    def test_connection_cycle(self):
        """
        Test connecting some node attributes.
        """
        utils.print_test_header("test_connection_cycle")

        n_1 = debug_nodes.EmptyNode()
        n_2 = debug_nodes.EmptyNode()
        n_3 = debug_nodes.EmptyNode()
        n_1.connect_attribute(constants.COMPLETED, n_2, constants.START)
        n_2.connect_attribute(constants.COMPLETED, n_3, constants.START)
        connection_status, _ = n_3.connect_attribute(
            constants.COMPLETED, n_1, constants.START
        )
        self.assertFalse(connection_status)

    def test_getting_internal_dict(self):
        """
        Test displaying the internal debug dict of a node
        """
        utils.print_test_header("test_getting_internal_dict")

        n_1 = general_input_nodes.StrInput()
        n_2 = general_nodes.GetDictKey()

        n_1.set_attribute_value("internal_str", "test")
        n_1.connect_attribute("out_str", n_2, "key")
        n_2.set_attribute_value("in_dict", {"test": 100})
        n_1.run_chain()

        assert n_2["out"].get_value() == 100

        pprint(n_2.get_node_full_dict())

    def test_inputs_checked_run(self):
        """
        Check all inputs of a node are properly set before starting to execute.
        """
        utils.print_test_header("test_inputs_checked_run")

        n_1 = debug_nodes.EmptyNode()
        n_1.run_single()
        self.assertEqual(n_1.success, constants.SUCCESSFUL)

        n_2 = file_reading_nodes.JsonToDict()
        n_2.run_single()
        self.assertEqual(n_2.success, constants.NOT_RUN)

        n_3 = file_writing_nodes.CreateTempFile()
        n_3.run_single()
        self.assertEqual(n_3.success, constants.SUCCESSFUL)

        n_4 = file_writing_nodes.CreateTempFile()
        n_4["suffix"].set_value(".txt")
        n_4.run_single()
        self.assertEqual(n_4.success, constants.SUCCESSFUL)

    def test_run_node_1(self):
        """
        Test the DictToYaml node
        """
        utils.print_test_header("test_run_node_1")

        temp = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False)
        temp.close()
        n_1 = file_writing_nodes.DictToYaml()
        n_1.set_attribute_value("in_dict", NodeTesting.DICT_EXAMPLE)
        n_1.set_attribute_value("yaml_filepath_to_write", temp.name)
        n_1._run()
        self.assertTrue(os.path.exists(temp.name))
        os.unlink(temp.name)
        self.assertFalse(os.path.exists(temp.name))

    def test_run_node_2(self):
        """
        Test the CreateTempFile node
        """
        utils.print_test_header("test_run_node_2")

        n_1 = file_writing_nodes.CreateTempFile()
        n_1._run()
        out_temp_path = n_1.get_attribute_value("tempfile_path")
        self.assertTrue(os.path.exists(out_temp_path))
        os.unlink(out_temp_path)
        self.assertFalse(os.path.exists(out_temp_path))

    def test_node_fails(self):
        """
        Test a case where a node should fail
        """
        utils.print_test_header("test_node_fails")

        n_1 = general_nodes.GetDictKey()
        n_1.set_attribute_value("in_dict", NodeTesting.DICT_EXAMPLE)
        n_1.set_attribute_value("key", "FAKE")
        n_1._run()

        self.assertEqual(n_1.success, constants.FAILED)

    def test_node_exception(self):
        """
        Test a case where a node should error and display the error
        """
        utils.print_test_header("test_node_exception")

        n_1 = debug_nodes.ErrorNode()
        n_1._run()

        self.assertEqual(n_1.success, constants.ERROR)

    def test_node_execution_time(self):
        """
        Test the execution time of nodes is being measured
        """
        utils.print_test_header("test_node_execution_time")

        n_1 = debug_nodes.TimedNode()
        n_1.run_single()

        self.assertGreater(n_1.execution_time, 1.0)
