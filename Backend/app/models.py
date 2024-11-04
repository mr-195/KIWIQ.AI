# myapp/models.py
from django.db import models
import json

class Node(models.Model):
    node_id = models.CharField(max_length=50, unique=True)
    data_in = models.JSONField(default=dict)
    data_out = models.JSONField(default=dict)

class Edge(models.Model):
    src_node = models.ForeignKey(Node, related_name='outgoing_edges', on_delete=models.CASCADE)
    dst_node = models.ForeignKey(Node, related_name='incoming_edges', on_delete=models.CASCADE)
    src_to_dst_data_keys = models.JSONField(null=True, blank=True)

class Graph(models.Model):
    nodes = models.ManyToManyField(Node)
    edges = models.ManyToManyField(Edge)

class RunConfig(models.Model):
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE)
    root_inputs = models.JSONField()
    data_overwrites = models.JSONField(null=True, blank=True)
    enable_list = models.JSONField(default=list)
    disable_list = models.JSONField(default=list)
