# myapp/serializers.py
from rest_framework import serializers
from .models import Node, Edge, Graph, RunConfig

class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = '__all__'

class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = '__all__'

class GraphSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True)
    edges = EdgeSerializer(many=True)

    class Meta:
        model = Graph
        fields = '__all__'

class RunConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RunConfig
        fields = '__all__'
