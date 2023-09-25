import unittest

from all_nodes import constants
from all_nodes.logic.logic_scene import LogicScene
from all_nodes.logic.logic_scene import LogicSceneError
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class ContextTesting(unittest.TestCase):
    def test_context_creation(self):
        """
        Create a context.
        """
        utils.print_test_header("test_context_creation")

        l = LogicScene()
        n_1 = l.add_node_by_name("EnvironToYmlCtx")
        self.assertIsNotNone(n_1)

    def test_fake_context_creation(self):
        """
        Try to create a context that does not exist.
        """
        utils.print_test_header("test_fake_context_creation")

        l = LogicScene()
        with self.assertRaises(LogicSceneError) as e:
            l.add_node_by_name("FakeCtx")
        print(e.exception)

    def test_context_run(self):
        """
        Create and run a context.
        """
        utils.print_test_header("test_context_run")

        l = LogicScene()
        n_1 = l.add_node_by_name("EnvironToYmlCtx")
        n_1.run_single()
        self.assertEqual(n_1.success, constants.SUCCESSFUL)

    def test_run_chain_from_ctx(self):
        """
        Run a chain of nodes starting at a context.
        """
        utils.print_test_header("test_run_chain_from_ctx")

        logic_scene = LogicScene()

        n_1 = logic_scene.add_node_by_name("EnvironToYmlCtx")
        n_2 = logic_scene.add_node_by_name("EmptyNode")
        n_1["COMPLETED"].connect_to_other(n_2["START"])

        n_1.run_chain()
