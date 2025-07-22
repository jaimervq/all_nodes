__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os
import unittest
import tempfile

from all_nodes import constants
from all_nodes.logic.logic_scene import LogicScene
from all_nodes.logic.logic_scene import LogicSceneError
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class LogicSceneTesting(unittest.TestCase):
    DICT_EXAMPLE = {
        "test_people": {"names": ["Fred", "Joe", "Sally"], "surnames": None}
    }

    FIXTURES_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures"
    )

    def test_logic_scene(self):
        """
        Create nodes in a logic scene
        """
        utils.print_test_header("test_logic_scene")

        logic_scene = LogicScene()
        logic_scene.add_node_by_name("JsonToDict")
        logic_scene.add_node_by_name("GetDictKey")
        logic_scene.add_node_by_name("GetDictKey")
        logic_scene.add_node_by_name("FailNode")
        self.assertEqual(logic_scene.node_count(), 4)

    def test_create_toml_nodes(self):
        """Create nodes registered in toml files"""
        utils.print_test_header("test_create_toml_nodes")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("UUID4Gen")
        n_2 = logic_scene.add_node_by_name("MathConstants")
        self.assertIn(".toml", n_1.FILEPATH)
        self.assertIn(".toml", n_2.FILEPATH)
        self.assertEqual(logic_scene.node_count(), 2)

    def test_run_node_graph_starting_at_node(self):
        utils.print_test_header("test_run_node_graph_starting_at_node")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("StrInput")
        n_1.set_attribute_value("internal_str", "test_people")
        n_2 = logic_scene.add_node_by_name("GetDictKey")
        n_2.set_attribute_value("in_dict", LogicSceneTesting.DICT_EXAMPLE)
        n_2["key"].connect_to_other(n_1["out_str"])
        n_3 = logic_scene.add_node_by_name("PrintToConsole")
        n_3["in_object_0"].connect_to_other(n_2["out"])
        n_1.run_chain()
        self.assertEqual(n_1.success, constants.SUCCESSFUL)
        self.assertEqual(n_2.success, constants.SUCCESSFUL)

    def test_locate_starting_nodes(self):
        utils.print_test_header("test_locate_starting_nodes")

        logic_scene = LogicScene()
        logic_scene.add_node_by_name("StrInput")
        n_2 = logic_scene.add_node_by_name("GetDictKey")
        logic_scene.add_node_by_name("PrintToConsole")
        logic_scene.add_node_by_name("CreateTempFile")
        n_5 = logic_scene.add_node_by_name("CreateTempFile")
        n_5[constants.START].connect_to_other(n_2[constants.COMPLETED])
        starting_nodes = logic_scene.get_starting_nodes()
        self.assertEqual(len(starting_nodes), 3)

    def test_locate_starting_nodes_2(self):
        utils.print_test_header("test_locate_starting_nodes_2")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("GetEnvVariable")
        n_1["env_variable_name"].set_value("USER")
        n_2 = logic_scene.add_node_by_name("PrintToConsole")
        n_1["env_variable_value"].connect_to_other(n_2["in_object_0"])
        starting_nodes = logic_scene.get_starting_nodes()
        self.assertEqual(len(starting_nodes), 1)

    def test_run_scene(self):
        utils.print_test_header("test_run_scene")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("GetEnvVariable")
        n_1["env_variable_name"].set_value("DUMMY_VAR")
        n_1["fallback_value"].set_value("NO_DUMMY_VAR_FOUND")
        n_2 = logic_scene.add_node_by_name("PrintToConsole")
        n_1["env_variable_value"].connect_to_other(n_2["in_object_0"])
        logic_scene.run_all_nodes_batch()
        self.assertEqual(n_1["env_variable_value"].get_value(), "NO_DUMMY_VAR_FOUND")
        self.assertEqual(n_1.success, constants.SUCCESSFUL)
        self.assertEqual(n_2.success, constants.SUCCESSFUL)

    def test_run_scene_with_notification(self):
        utils.print_test_header("run_scene_with_notification")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("EmptyNode")
        n_2 = logic_scene.add_node_by_name("SendPushNotification")
        n_2["title"].set_value("⚙️ Test notification")
        n_2["body"].set_value("[LOCAL] all_nodes tests are running...")
        if os.getenv("GITHUB_ACTIONS"):
            n_2["body"].set_value(
                f"[GITHUB {os.getenv('GITHUB_RUN_ID')}]\nall_nodes tests are running..."
            )
        n_2[constants.START].connect_to_other(n_1[constants.COMPLETED])
        logic_scene.run_all_nodes_batch()
        self.assertEqual(n_1.success, constants.SUCCESSFUL)
        self.assertEqual(n_2.success, constants.SUCCESSFUL)
        self.assertEqual(n_2["status_code"].get_value(), 200)

    def test_capture_node(self):
        utils.print_test_header("test_capture_node")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("StrInput")
        full_name = n_1.node_name
        n_2 = logic_scene.to_node(full_name)
        self.assertEqual(n_1, n_2)

    def test_run_scene_with_disabled(self):
        utils.print_test_header("test_run_scene_with_disabled")

        logic_scene = LogicScene()
        logic_scene.load_from_file("fail_scene")
        logic_scene.run_all_nodes_batch()

        n = logic_scene.to_node("EmptyNode_2")
        self.assertEqual(n.success, constants.SKIPPED)
        self.assertFalse(n.active)

    def test_write_scene_to_file(self):
        utils.print_test_header("test_write_scene_to_file")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("StrInput")
        n_1.set_attribute_value("internal_str", "TEST")
        n_2 = logic_scene.add_node_by_name("PrintToConsole")
        n_1["out_str"].connect_to_other(n_2["in_object_0"])
        n_2[constants.START].connect_to_other(n_1[constants.COMPLETED])
        logic_scene.run_all_nodes_batch()

        temp = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False)
        temp.close()
        logic_scene.save_to_file(temp.name)

        self.assertTrue(os.path.isfile(temp.name))
        self.assertTrue(n_1.success, constants.SUCCESSFUL)

    def test_load_scene_from_file(self):
        utils.print_test_header("test_load_scene_from_file")

        logic_scene = LogicScene()
        logic_scene.load_from_file(
            os.path.join(self.FIXTURES_FOLDER, "environ_to_yaml_and_json.yml")
        )
        self.assertEqual(logic_scene.node_count(), 9)

    def test_load_scene_from_file_faulty(self):
        utils.print_test_header("test_load_scene_from_file_2")

        logic_scene = LogicScene()
        with self.assertRaises(LogicSceneError) as e:
            logic_scene.load_from_file(
                os.path.join(self.FIXTURES_FOLDER, "faulty_scene.yml")
            )
        print(e.exception)

    def test_load_scene_from_file_faulty_2(self):
        utils.print_test_header("test_load_scene_from_file_3")

        logic_scene = LogicScene()
        with self.assertRaises(LogicSceneError) as e:
            logic_scene.load_from_file(
                os.path.join(self.FIXTURES_FOLDER, "faulty_scene_2.yml")
            )
        print(e.exception)

    def test_load_scene_from_alias(self):
        utils.print_test_header("test_load_scene_from_alias")

        logic_scene = LogicScene()
        logic_scene.load_from_file("env_variables")

    def test_load_scene_from_alias_faulty(self):
        utils.print_test_header("test_load_scene_from_alias_faulty")

        logic_scene = LogicScene()
        with self.assertRaises(LogicSceneError) as e:
            logic_scene.load_from_file("fake_scene")
        print(e.exception)

    def test_execute_scene_from_alias(self):
        utils.print_test_header("test_execute_scene_from_alias")

        logic_scene = LogicScene()
        logic_scene.load_from_file("env_variables")
        logic_scene.run_all_nodes_batch()

        assert len(logic_scene.gather_failed_nodes_logs()) == 1
        assert len(logic_scene.gather_errored_nodes_logs()) == 0

    def test_execute_scene_from_alias_2(self):
        utils.print_test_header("test_execute_scene_from_alias_2")

        logic_scene = LogicScene()
        logic_scene.load_from_file("environ_to_yaml")
        logic_scene.run_all_nodes_batch()

        assert len(logic_scene.gather_failed_nodes_logs()) == 0
        assert len(logic_scene.gather_errored_nodes_logs()) == 0

    def test_execute_scene_from_alias_3(self):
        utils.print_test_header("test_execute_scene_from_alias_3")

        logic_scene = LogicScene()
        logic_scene.load_from_file("fail_scene")
        logic_scene.run_all_nodes_batch()

        assert len(logic_scene.gather_failed_nodes_logs()) == 3
        assert len(logic_scene.gather_errored_nodes_logs()) == 3

    def test_execute_scene_from_alias_4(self):
        utils.print_test_header("test_execute_scene_from_alias_4")

        logic_scene = LogicScene()
        logic_scene.load_from_file("datetime_example")
        logic_scene.run_all_nodes_batch()

        assert len(logic_scene.gather_failed_nodes_logs()) == 0
        assert len(logic_scene.gather_errored_nodes_logs()) == 0

    def test_rename_node_incorrect(self):
        utils.print_test_header("test_rename_node_incorrect")

        logic_scene = LogicScene()
        n = logic_scene.add_node_by_name("PrintToConsole")
        result = logic_scene.rename_node(n, "Bad_name_*?")
        self.assertFalse(result)

    def test_rename_node_already_present(self):
        utils.print_test_header("test_rename_node_already_present")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("PrintToConsole")
        n_2 = logic_scene.add_node_by_name("YamlToDict")
        self.assertFalse(logic_scene.rename_node(n_1, n_2.node_name))

    def test_scene_with_loop(self):
        utils.print_test_header("test_scene_with_loop")

        logic_scene = LogicScene()
        logic_scene.load_from_file("loop_example")
        logic_scene.run_all_nodes_batch()

        foreach_begin = logic_scene.to_node("ForEachBegin_1")
        assert foreach_begin.execution_counter == 1

        print_1 = logic_scene.to_node("PrintToConsole_1")
        assert print_1.execution_counter == 3

        print_2 = logic_scene.to_node("PrintToConsole_2")
        assert print_2.execution_counter == 3

        foreach_end = logic_scene.to_node("ForEachEnd_1")
        assert foreach_end.execution_counter == 1

        empty_node_2 = logic_scene.to_node("EmptyNode_2")
        assert empty_node_2.execution_counter == 1
