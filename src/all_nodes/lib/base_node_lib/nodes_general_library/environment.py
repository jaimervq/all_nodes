# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class GetEntireEnviron(GeneralLogicNode):
    NICE_NAME = "Get entire environment"

    OUTPUTS_DICT = {"environ_dict": {"type": dict}}

    def run(self):
        import os

        self.set_output("environ_dict", dict(os.environ))


class GetEnvVariable(GeneralLogicNode):
    NICE_NAME = "Get env variable"
    HELP = (
        "Get the value of an environment variable, with possibility of a fallback "
        "value if the variable is not defined"
    )

    INPUTS_DICT = {
        "env_variable_name": {"type": str},
        "fallback_value": {"type": str, "optional": True},
    }

    OUTPUTS_DICT = {"env_variable_value": {"type": str}}

    def run(self):
        import os

        env_variable_name = self.get_attribute_value("env_variable_name")
        fallback_value = self.get_attribute_value("fallback_value")
        env_var_value = os.getenv(env_variable_name)
        if env_var_value is None:
            if fallback_value:
                env_var_value = fallback_value
            else:
                self.fail(
                    "No environment variable '{}' found".format(env_variable_name)
                )
                return

        self.set_output("env_variable_value", env_var_value)


class SetEnvVariable(GeneralLogicNode):
    INPUTS_DICT = {
        "env_variable_name": {"type": str},
        "new_value": {"type": str},
    }

    def run(self):
        import os

        env_variable_name = self.get_attribute_value("env_variable_name")
        new_value = self.get_attribute_value("new_value")

        os.environ[env_variable_name] = new_value
