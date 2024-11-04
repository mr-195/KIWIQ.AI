# myapp/graph_execution.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

@dataclass
class Edge:
    src_node: 'Node'
    dst_node: 'Node'
    src_to_dst_data_keys: Optional[Dict[str, str]] = None

@dataclass
class Node:
    node_id: str
    data_in: Dict[str, any] = field(default_factory=dict)
    data_out: Dict[str, any] = field(default_factory=dict)
    incoming_edges: List[Edge] = field(default_factory=list)
    outgoing_edges: List[Edge] = field(default_factory=list)

class DAG:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def add_node(self, node_id: str) -> Node:
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id=node_id)
        return self.nodes[node_id]

    def add_edge(self, src_id: str, dst_id: str, src_to_dst_data_keys: Optional[Dict[str, str]] = None) -> Edge:
        src_node = self.add_node(src_id)
        dst_node = self.add_node(dst_id)
        
        edge = Edge(src_node=src_node, dst_node=dst_node, src_to_dst_data_keys=src_to_dst_data_keys)
        src_node.outgoing_edges.append(edge)
        dst_node.incoming_edges.append(edge)
        return edge

    def _get_node_levels(self) -> Dict[str, int]:
        levels = {}
        visited = set()

        def dfs(node_id: str, level: int):
            if node_id in visited:
                return
            visited.add(node_id)
            levels[node_id] = max(levels.get(node_id, 0), level)
            node = self.nodes[node_id]
            for edge in node.outgoing_edges:
                dfs(edge.dst_node.node_id, level + 1)

        root_nodes = [node_id for node_id, node in self.nodes.items() if not node.incoming_edges]
        for root in root_nodes:
            dfs(root, 0)

        return levels

    def process_data_flow(self) -> None:
        levels = self._get_node_levels()
        level_to_nodes = defaultdict(list)
        for node_id, level in levels.items():
            level_to_nodes[level].append(node_id)

        for level in sorted(level_to_nodes.keys()):
            level_nodes = sorted(level_to_nodes[level])
            for node_id in level_nodes:
                node = self.nodes[node_id]
                dst_key_sources: Dict[str, Tuple[int, str, any]] = {}
                for edge in node.incoming_edges:
                    if not edge.src_to_dst_data_keys:
                        continue
                    src_node = edge.src_node
                    src_level = levels[src_node.node_id]
                    for src_key, dst_key in edge.src_to_dst_data_keys.items():
                        if src_key not in src_node.data_out:
                            continue
                        value = src_node.data_out[src_key]
                        if dst_key not in dst_key_sources:
                            dst_key_sources[dst_key] = (src_level, src_node.node_id, value)
                        else:
                            curr_level, curr_id, _ = dst_key_sources[dst_key]
                            if (src_level > curr_level) or \
                               (src_level == curr_level and src_node.node_id < curr_id):
                                dst_key_sources[dst_key] = (src_level, src_node.node_id, value)
                for dst_key, (_, _, value) in dst_key_sources.items():
                    node.data_in[dst_key] = value
