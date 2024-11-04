from typing import List, Dict, Union, Optional
from collections import deque
import uuid

# Define types for data
DataType = Union[int, float, str, bool, list, dict]

class Edge:
    def __init__(self, src_node: str, dst_node: str, src_to_dst_data_keys: Dict[str, str] = None):
        self.src_node = src_node
        self.dst_node = dst_node
        self.src_to_dst_data_keys = src_to_dst_data_keys or {}

class Node:
    def __init__(self, node_id: str, data: Dict[str, DataType] = None):
        self.node_id = node_id
        self.data = data or {}
        self.paths_in: List[Edge] = []
        self.paths_out: List[Edge] = []

class GraphRunConfig:
    def __init__(self, root_inputs: Dict[str, Dict[str, DataType]] = None, 
                 data_overwrites: Dict[str, Dict[str, DataType]] = None,
                 enable_list: Optional[List[str]] = None,
                 disable_list: Optional[List[str]] = None):
        self.root_inputs = root_inputs or {}
        self.data_overwrites = data_overwrites or {}
        self.enable_list = enable_list
        self.disable_list = disable_list

class Graph:
    def __init__(self, nodes: List[Node]):
        self.nodes = {node.node_id: node for node in nodes}
        self._validate_graph_structure()

    def _validate_graph_structure(self):
        if len(self.nodes) != len(set(node.node_id for node in self.nodes.values())):
            raise ValueError("Duplicate node IDs found in graph")
        # print("HERE");
        for node in self.nodes.values():
            for edge in node.paths_out:
                dst_node = self.nodes.get(edge.dst_node)
                if dst_node is None:
                    raise ValueError(f"Node {edge.dst_node} does not exist in the graph")
                
                for src_key, dst_key in edge.src_to_dst_data_keys.items():
                    if src_key in node.data and dst_key in dst_node.data:
                        # print("type(node.data[src_key])", type(node.data[src_key]));
                        # print("type(dst_node.data[dst_key])", type(dst_node.data[dst_key]));
                        if type(dst_node.data[dst_key])==None or type(node.data[src_key]) != type(dst_node.data[dst_key]):
                            raise ValueError(f"Incompatible data types for {src_key} -> {dst_key}")

            outgoing_edges = {(e.src_node, e.dst_node): e for e in node.paths_out}
            if len(outgoing_edges) != len(node.paths_out):
                raise ValueError("Duplicate edges found in graph")

    def _detect_cycle(self):
        visited = {}
        stack = {}

        def dfs(node_id):
            if visited.get(node_id, False):
                return False
            if stack.get(node_id, False):
                return True
            stack[node_id] = True
            for edge in self.nodes[node_id].paths_out:
                if dfs(edge.dst_node):
                    return True
            stack[node_id] = False
            visited[node_id] = True
            return False

        for node_id in self.nodes:
            if not visited.get(node_id, False):
                if dfs(node_id):
                    raise ValueError("Cycle detected in the graph")

    def run(self, config: GraphRunConfig):
        self._validate_config(config)
        self._detect_cycle()
        run_id = str(uuid.uuid4())
        
        enabled_nodes = self._get_enabled_nodes(config)
        self._populate_root_inputs(config, enabled_nodes)
        self._propagate_data(enabled_nodes, config)

        return run_id

    def _validate_config(self, config: GraphRunConfig):
        if config.enable_list and config.disable_list:
            raise ValueError("Cannot provide both enable_list and disable_list")

    def _get_enabled_nodes(self, config: GraphRunConfig):
        if config.enable_list:
            return {node_id: self.nodes[node_id] for node_id in config.enable_list if node_id in self.nodes}
        elif config.disable_list:
            return {node_id: self.nodes[node_id] for node_id in self.nodes if node_id not in config.disable_list}
        else:
            return self.nodes

    def _populate_root_inputs(self, config: GraphRunConfig, enabled_nodes: Dict[str, Node]):
        for node_id, data in config.root_inputs.items():
            if node_id in enabled_nodes:
                enabled_nodes[node_id].data.update(data)

    def _propagate_data(self, enabled_nodes: Dict[str, Node], config: GraphRunConfig):
        levels = self.toposort(enabled_nodes)
        # print("levels", levels)
        # print data in all nodes
        for level in levels:
            for node_id in level:
                node = enabled_nodes[node_id]
                if node_id in config.data_overwrites:
                    node.data.update(config.data_overwrites[node_id])
        # for node in enabled_nodes.values():
        #     print("node.data", node.data)
        for level in levels:
            for node_id in level:
                node = enabled_nodes[node_id]

                for edge in node.paths_out:
                    dst_node = enabled_nodes.get(edge.dst_node)
                    if dst_node:
                        for src_key, dst_key in edge.src_to_dst_data_keys.items():
                            dst_node.data[dst_key] = node.data[src_key]

    def toposort(self, enabled_nodes: Dict[str, Node]):
        in_degree = {node_id: 0 for node_id in enabled_nodes}
        for node in enabled_nodes.values():
            for edge in node.paths_out:
                if edge.dst_node in in_degree:
                    in_degree[edge.dst_node] += 1
        zero_in_degree = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        levels = []
        while zero_in_degree:
            level = []
            for _ in range(len(zero_in_degree)):
                node_id = zero_in_degree.popleft()
                level.append(node_id)
                for edge in enabled_nodes[node_id].paths_out:
                    if edge.dst_node in in_degree:
                        in_degree[edge.dst_node] -= 1
                        if in_degree[edge.dst_node] == 0:
                            zero_in_degree.append(edge.dst_node)
            levels.append(level)
        return levels

    def get_data(self, run_id: str, node_id: str) -> Dict[str, DataType]:
        if node_id in self.nodes:
            return self.nodes[node_id].data
        else:
            raise ValueError(f"Node {node_id} not found in the graph")

    def get_leaf_outputs(self, run_id: str) -> Dict[str, Dict[str, DataType]]:
        leaf_nodes = [node_id for node_id, node in self.nodes.items() if not node.paths_out]
        return {node_id: self.nodes[node_id].data for node_id in leaf_nodes}

    def get_islands(self, config: GraphRunConfig) -> List[List[str]]:
        enabled_nodes = self._get_enabled_nodes(config)
        visited = set()
        islands = []

        def dfs(node_id, island):
            visited.add(node_id)
            island.append(node_id)
            for edge in self.nodes[node_id].paths_out:
                if edge.dst_node in enabled_nodes and edge.dst_node not in visited:
                    dfs(edge.dst_node, island)
            for edge in self.nodes[node_id].paths_in:
                if edge.src_node in enabled_nodes and edge.src_node not in visited:
                    dfs(edge.src_node, island)

        for node_id in enabled_nodes:
            if node_id not in visited:
                island = []
                dfs(node_id, island)
                islands.append(island)

        return islands
    
# TESTS
def test_graph_initialization():
    node_a = Node(node_id="A", data={"key": 10})
    node_b = Node(node_id="B", data={"key": 20})
    node_c = Node(node_id="C", data={"key": 30})

    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    edge_bc = Edge(src_node="B", dst_node="C", src_to_dst_data_keys={"key": "key"})

    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)
    node_b.paths_out.append(edge_bc)
    node_c.paths_in.append(edge_bc)

    graph = Graph(nodes=[node_a, node_b, node_c])

    assert "A" in graph.nodes
    assert "B" in graph.nodes
    assert "C" in graph.nodes
    print("test_graph_initialization passed")

def test_run_graph_basic_propagation():
    node_a = Node(node_id="A", data={"key": 10})
    node_b = Node(node_id="B", data={"key": 20})
    node_c = Node(node_id="C", data={"key": 20})

    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    edge_bc = Edge(src_node="B", dst_node="C", src_to_dst_data_keys={"key": "key"})

    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)
    node_b.paths_out.append(edge_bc)
    node_c.paths_in.append(edge_bc)

    graph = Graph(nodes=[node_a, node_b, node_c])

    config = GraphRunConfig(root_inputs={"A": {"key": 10}})
    run_id = graph.run(config)

    assert graph.get_data(run_id, "A")["key"] == 10
    assert graph.get_data(run_id, "B")["key"] == 10
    assert graph.get_data(run_id, "C")["key"] == 10
    print("test_run_graph_basic_propagation passed")

def test_graph_with_root_inputs_and_overwrites():
    node_a = Node(node_id="A", data={"key": 15})
    node_b = Node(node_id="B", data={"key": 0})
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)

    graph = Graph(nodes=[node_a, node_b])
    config = GraphRunConfig(root_inputs={"A": {"key": 10}}, data_overwrites={"A": {"key": 20}})
    run_id = graph.run(config)
    assert graph.get_data(run_id, "A")["key"] == 20
    print("test_graph_with_root_inputs_and_overwrites passed")
    
    
def test_graph_with_multiple_inputs():
    node_a = Node(node_id="A", data={"key": 15})
    node_b = Node(node_id="B", data={"key": 0})
    node_c = Node(node_id="C", data={"key": 0})
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    edge_ac = Edge(src_node="A", dst_node="C", src_to_dst_data_keys={"key": "key"})
    node_a.paths_out.append(edge_ab)
    node_a.paths_out.append(edge_ac)
    node_b.paths_in.append(edge_ab)
    node_c.paths_in.append(edge_ac) 
    
    graph = Graph(nodes=[node_a, node_b, node_c])
    config = GraphRunConfig(root_inputs={"A": {"key": 10}}, data_overwrites={"A": {"key": 20}})
    run_id = graph.run(config)
    # print("graph.get_data(run_id, 'A')", graph.get_data(run_id, "A"))
    # print("graph.get_data(run_id, 'B')", graph.get_data(run_id, "B"))
    # print("graph.get_data(run_id, 'C')", graph.get_data(run_id, "C"))
    assert graph.get_data(run_id, "A")["key"] == 20
    assert graph.get_data(run_id, "B")["key"] == 20
    assert graph.get_data(run_id, "C")["key"] == 20
    print("test_graph_with_multiple_inputs passed")
    
def test_graph_with_multiple_inputs_and_overwrites():
    # Create a diamond-shaped graph with multiple overwrites
    node_a = Node(node_id="A", data={"key": 15})
    node_b = Node(node_id="B", data={"key": 0})
    node_c = Node(node_id="C", data={"key": 0})
    node_d = Node(node_id="D", data={"key": 0})     
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    edge_ac = Edge(src_node="A", dst_node="C", src_to_dst_data_keys={"key": "key"})
    edge_bd = Edge(src_node="B", dst_node="D", src_to_dst_data_keys={"key": "key"})
    edge_cd = Edge(src_node="C", dst_node="D", src_to_dst_data_keys={"key": "key"})
    edge_bd_dependency = Edge(src_node="B", dst_node="D")
    
    node_a.paths_out.extend([edge_ab, edge_ac])
    node_b.paths_out.append(edge_bd)
    node_c.paths_out.append(edge_cd)
    node_b.paths_in.append(edge_ab)
    node_c.paths_in.append(edge_ac)
    node_d.paths_in.extend([edge_bd, edge_cd, edge_bd_dependency])
    
    graph = Graph(nodes=[node_a, node_b, node_c, node_d])
    config = GraphRunConfig(
        root_inputs={"A": {"key": 10}},
        data_overwrites={
            "A": {"key": 20},
            "B": {"key": 30},
            "C": {"key": 40}
        }
    )
    run_id = graph.run(config)
    
    # print("graph.get_data(run_id, 'A')", graph.get_data(run_id, "A"))
    # print("graph.get_data(run_id, 'B')", graph.get_data(run_id, "B"))
    # print("graph.get_data(run_id, 'C')", graph.get_data(run_id, "C"))
    # print("graph.get_data(run_id, 'D')", graph.get_data(run_id, "D"))
    
    assert graph.get_data(run_id, "A")["key"] == 20
    assert graph.get_data(run_id, "B")["key"] == 20
    assert graph.get_data(run_id, "C")["key"] == 20
    assert graph.get_data(run_id, "D")["key"] == 20  # B's value should propagate to D
    
    print("test_graph_with_multiple_inputs_and_overwrites passed")

def test_overrites_from_different_levels():
    node_a = Node(node_id="A", data={"key": 15})
    node_b = Node(node_id="B", data={"key": 0}) 
    node_c = Node(node_id="C", data={"key": 0})
    node_d = Node(node_id="D", data={"key": 0})
    node_e = Node(node_id="E", data={"key": 0})
    
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    edge_ac = Edge(src_node="A", dst_node="C", src_to_dst_data_keys={"key": "key"})
    edge_cd = Edge(src_node="C", dst_node="D", src_to_dst_data_keys={"key": "key"})
    edge_ad = Edge(src_node="A", dst_node="D", src_to_dst_data_keys={"key": "key"})
    edge_ed = Edge(src_node="E", dst_node="D", src_to_dst_data_keys={"key": "key"})
    
    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)
    node_a.paths_out.append(edge_ac)
    node_c.paths_in.append(edge_ac)
    node_c.paths_out.append(edge_cd)
    node_d.paths_in.append(edge_cd)
    node_a.paths_out.append(edge_ad)
    node_d.paths_in.append(edge_ad)
    node_e.paths_out.append(edge_ed)
    graph = Graph(nodes=[node_a, node_b, node_c, node_d, node_e])
    config = GraphRunConfig(
        root_inputs={"A": {"key": 10},"E": {"key": 20}},
    )
    run_id = graph.run(config)
    # print("graph.get_data(run_id, 'A')", graph.get_data(run_id, "A"))
    # print("graph.get_data(run_id, 'B')", graph.get_data(run_id, "B"))
    # print("graph.get_data(run_id, 'C')", graph.get_data(run_id, "C"))
    # print("graph.get_data(run_id, 'D')", graph.get_data(run_id, "D"))
    # print("graph.get_data(run_id, 'E')", graph.get_data(run_id, "E"))
    assert graph.get_data(run_id, "A")["key"] == 10
    assert graph.get_data(run_id, "B")["key"] == 10
    assert graph.get_data(run_id, "C")["key"] == 10
    assert graph.get_data(run_id, "D")["key"] == 10
    assert graph.get_data(run_id, "E")["key"] == 20
    print("test_overrites_from_different_levels passed")

def test_with_multiple_keys():
    node_a = Node(node_id="A", data={"key": 10, "key2": "HEY"})
    node_b = Node(node_id="B", data={"key": 0, "key2": "Hi"})
    node_c = Node(node_id="C", data={"key": 0, "key2": "Hello"})
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key", "key2": "key2"})
    edge_bc = Edge(src_node="B", dst_node="C", src_to_dst_data_keys={"key": "key", "key2": "key2"})
    edge_ac = Edge(src_node="A", dst_node="C", src_to_dst_data_keys={"key": "key", "key2": "key2"})
    
    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)
    node_b.paths_out.append(edge_bc)
    node_c.paths_in.append(edge_bc)
    node_a.paths_out.append(edge_ac)
    node_c.paths_in.append(edge_ac)
    graph = Graph(nodes=[node_a, node_b, node_c])
    config = GraphRunConfig(
        root_inputs={"A": {"key": 10, "key2": "HEY"}},
    )
    run_id = graph.run(config)
    # print("graph.get_data(run_id, 'A')", graph.get_data(run_id, "A"))
    # print("graph.get_data(run_id, 'B')", graph.get_data(run_id, "B"))
    # print("graph.get_data(run_id, 'C')", graph.get_data(run_id, "C"))
    assert graph.get_data(run_id, "A")["key"] == 10
    assert graph.get_data(run_id, "A")["key2"] == "HEY"
    assert graph.get_data(run_id, "B")["key"] == 10
    assert graph.get_data(run_id, "B")["key2"] == "HEY"
    assert graph.get_data(run_id, "C")["key"] == 10
    assert graph.get_data(run_id, "C")["key2"] == "HEY"
    print("test_with_multiple_keys passed")
    
# These tests are for error handling
    
    
def test_with_cycle():
    node_a = Node(node_id="A", data={"key": 10})
    node_b = Node(node_id="B", data={"key": 0})
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    edge_ba = Edge(src_node="B", dst_node="A", src_to_dst_data_keys={"key": "key"})
    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)
    node_b.paths_out.append(edge_ba)
    node_a.paths_in.append(edge_ba)
    graph = Graph(nodes=[node_a, node_b])
    config = GraphRunConfig(root_inputs={"A": {"key": 10}})
    try:
        graph.run(config)
    except ValueError as e:
        assert str(e) == "Cycle detected in the graph"
    print("test_with_cycle passed")
    
def test_with_incompatible_types():
    node_a = Node(node_id="A", data={"key": 10})
    node_b = Node(node_id="B", data={"key": 0})
    edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
    node_a.paths_out.append(edge_ab)
    node_b.paths_in.append(edge_ab)
    graph = Graph(nodes=[node_a, node_b])
    config = GraphRunConfig(root_inputs={"A": {"key": 10}})
    try:
        graph.run(config)
    except ValueError as e:
        assert str(e) == "Incompatible data types for key -> key"
    print("test_with_incompatible_types passed")
    
def test_with_duplicate_edges():
    try:    
        node_a = Node(node_id="A", data={"key": 10})
        node_b = Node(node_id="B", data={"key": 0})
        edge_ab = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
        edge_ab_duplicate = Edge(src_node="A", dst_node="B", src_to_dst_data_keys={"key": "key"})
        node_a.paths_out.append(edge_ab)
        node_b.paths_in.append(edge_ab)
        node_a.paths_out.append(edge_ab_duplicate)
        node_b.paths_in.append(edge_ab_duplicate)        
        graph = Graph(nodes=[node_a, node_b])   
        config = GraphRunConfig(root_inputs={"A": {"key": 10}})
        graph.run(config)
    except ValueError as e:
        assert str(e) == "Duplicate edges found in graph"
    print("test_with_duplicate_edges passed")   
    
def run_tests():
    test_graph_initialization()
    test_run_graph_basic_propagation()
    test_graph_with_root_inputs_and_overwrites()
    test_graph_with_multiple_inputs()
    test_graph_with_multiple_inputs_and_overwrites()
    test_overrites_from_different_levels()
    test_with_multiple_keys()
    test_with_cycle()
    test_with_incompatible_types()
    test_with_duplicate_edges()
    
if __name__ == "__main__":
    run_tests()