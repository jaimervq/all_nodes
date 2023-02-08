# all_nodes
**all_nodes** is a node editor designed to be used in the most flexible way possible.

Some of its main goals are:
* Prevent code from being re-written, duplicated
* Make debugging tasks easier, by using a one-node-at-a-time process
* Provide a nice graphic scene where node networks can be examined, modified, etc

![](documentation/preview_1.png)

## Adding more classes/nodes
The places where all_nodes will search for node classes, scenes, etc is defined by the environment variable **ALL_NODES_LIB_PATH**

## Folder structure example
Example of organization of a folder, that contains two libraries

| Folder structure                      | Classes representation                   | Scenes                                |
|---------------------------------------|------------------------------------------|---------------------------------------|
| ![](documentation/folder_example.png) | ![](documentation/structure_example.png) | ![](documentation/scenes_example.png) |                              

Each library can have as many modules as needed, and can have an 'icons' folder to provide icons for the classes contained in the modules.

## Defining a node
Inside each module, nodes/classes can be defined as easy as this:

```python
class GetEnvVariable(GeneralLogicNode):
    
    NICE_NAME = "Get env variable"
    HELP = "Get the value of an environment variable, with possibility of a fallback" \
           "value if the variable is not defined"

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
```

Key elements that a node **MUST** have:
* A very unique name to itself, that cleary indicates what it does
* A `run` method

Key elements that a node **CAN** have:
* A `NICE_NAME` attribute, for this node to be displayed more readable
* A `HELP` attribute to explain how the node works
* The `INPUTS_DICT` dictionary, if the node needs inputs
* The `OUTPUTS_DICT` dictionary, if the node needs outputs

Other considerations:
* The `import` statements are kept inside the run method, so no ImportError is met when editing DCC-specific nodes outside the DCC they are meant for.

## Defining a context
![](documentation/context.png)

A context is a "node of nodes", or a node that contains a scene inside itself. To define it, just two ingredients are needed:
* As usual, a class in a .py file, with the **IS_CONTEXT** attribute set
* In the same folder as the .py file, a .ctx file (just a yaml file but with that extension instead) with the inner scene of the node

Once "inside" the context, its input attributes can be "grabbed" and its output attributes set by making use of the special ctx nodes:
![](documentation/ctx_grab.png)

## Defining a scene
Defining a scene is very easy, it is a simple and readable yaml file.

To look for scenes, all_nodes will:
* Examine each path defined in **ALL_NODES_LIB_PATH**
* Then in that path, will look for a folder that contains **"scene_lib"** in its name
* From that folder, will recursively scan for and add all .yml files found

Example of scene:
```yaml
# SCENE environ_to_yaml
# ---------------------
# Description: Simple scene to write the environ out to a yaml file

# Nodes section: overall list of nodes to be created
nodes:
- EnvironToYmlCtx_1:
    class_name: EnvironToYmlCtx
    x_pos: -904
    y_pos: -284
- StartFile_1:
    class_name: StartFile
    x_pos: -611
    y_pos: -304

# Connections section: connections to be done between nodes
connections:
- EnvironToYmlCtx_1.yaml_filepath -> StartFile_1.file_path


# Scene created at: 2023-01-24 23:13:10.371378
# Created by: jaime.rvq
```

The scene just needs two keys:
* **nodes**: with a list of nodes to be created
* **connections**: to establish the connections between the created nodes

Note how the **->** symbol is used to make the connections section more easily readable.

## Batch execution
Any .yml scene file can be executed in batch mode without the need to open the graphic editor.

This can be done by launching the main file and making use of the **-f** flag.

Example: `main.py -f D:/scene_examples/my_scene.yml`

Also, when a scene belongs to a repo/folder that has been defined in the **ALL_NODES_LIB_PATH** variable, it can be found just by its "alias". This alias is just the file name, with no need for the complete path or the ,yml extension.

Example: `main.py -f environ_to_yaml`

## Execution order of nodes
In a scene, the execution starts from nodes that are recognized as "starting nodes".
Those are nodes that:
* Have no dependency/inputs/connetions from others.
* Don't have any non-optional attributes not set

![](documentation/start_nodes.png)

In these example nodes, none of them have any incoming connections. Also, the only input attribute they all have is the START attribute, but since it is an optional attribute, the node can start executing even if it is not set.
  
Another example:

![](documentation/start_node_manual.png)

The node has a non-optional input. It is not connected, but a value has been defined to it, so the node can start executing.

### Examples of execution order after the starting nodes
When a start node is executed, and it is successful, the nodes connected to its outputs will try to execute as well.
Have a look at this example:

![](documentation/exec_1.png)

What will happen is:
* IntInput_1 is executed
* It is successful, so its output value "out_int" is propagated to the connected nodes
* IntInput_1 now launches the execution of the connected nodes
* The connected nodes are executed in random order. This time it starts with IntToStr_1
* IntToStr_1 runs successfully
* IntToStr_2 is executed, runs successfully

However, changing the scene a little bit, makes things  more complex:

![](documentation/exec_2.png)

* IntInput_1 is executed
* It is successful, so its output value "out_int" is propagated to the connected nodes. Also, this time the "COMPLETED" attribute is propagated to the EmptyNode_1 connected node.
* IntInput_1 now launches the execution of the connected nodes
* The connected nodes are executed in random order. It has 3 connected nodes. This time it starts with IntToStr_2
* IntToStr_2 runs successfully
* IntToStr_1 is attempted to be executed, but has not recieved a value in its START attribute. It will not run now.
* EmptyNode_1 runs successfully. It propagates its COMPLETED value to IntToStr_1.
* EmptyNode_1 now launches the execution of its only connected node, IntToStr_1.
* IntToStr_1 now has all its connected inputs set, it can be executed. It runs successfully

## Create and run node networks on the fly
For simple setups and tests, node networks can be created and run at the same time in a python script.

Example:
```python
from all_nodes.logic.logic_scene import LogicScene


l_scene = LogicScene()

n_1 = l_scene.add_node_by_name("EmptyNode")
n_2 = l_scene.add_node_by_name("EmptyNode")
n_1["COMPLETED"].connect_to_other(n_2["START"])

l_scene.run_all_nodes()
```

## Some library repos
### Maya:
* https://gitlab.com/python-3/maya/maya_all_nodes_lib
### Nuke:
* https://gitlab.com/python-3/nuke/nuke_all_nodes_lib
### Houdini
* https://gitlab.com/python-3/houdini/houdini_all_nodes_lib