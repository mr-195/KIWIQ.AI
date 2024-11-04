# myapp/views.py
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Graph, Node, Edge, RunConfig
from .serializers import GraphSerializer, NodeSerializer, EdgeSerializer, RunConfigSerializer
from .graph_execution import DAG

class GraphViewSet(viewsets.ModelViewSet):
    queryset = Graph.objects.all()
    serializer_class = GraphSerializer

class RunConfigViewSet(viewsets.ModelViewSet):
    queryset = RunConfig.objects.all()
    serializer_class = RunConfigSerializer

    def perform_create(self, serializer):
        graph = serializer.validated_data['graph']
        dag = DAG()
        for node in graph.nodes.all():
            dag.add_node(node.node_id)
            node_data_out = json.loads(node.data_out)
            dag.nodes[node.node_id].data_out.update(node_data_out)

        for edge in graph.edges.all():
            dag.add_edge(edge.src_node.node_id, edge.dst_node.node_id, edge.src_to_dst_data_keys)

        dag.process_data_flow()
        serializer.save()


from .models import Node
from .serializers import NodeSerializer

class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    
class EdgeViewSet(viewsets.ModelViewSet):
    queryset = Edge.objects.all()
    serializer_class = EdgeSerializer