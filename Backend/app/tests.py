# app/tests.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from app.models import Node, Edge, Graph, RunConfig
from app.serializers import NodeSerializer, EdgeSerializer, GraphSerializer, RunConfigSerializer

class GraphAPITestCase(APITestCase):
    def setUp(self):
        # Set up initial test data if necessary
        self.graph = Graph.objects.create(name="Test Graph")
        self.node_a = Node.objects.create(node_id="A", graph=self.graph)
        self.node_b = Node.objects.create(node_id="B", graph=self.graph)
        self.edge = Edge.objects.create(
            src_node=self.node_a,
            dst_node=self.node_b,
            src_to_dst_data_keys={"out1": "in1"}
        )

    def test_create_node(self):
        """Test creating a new node"""
        url = reverse('node-list')  # Ensure the name matches your URL conf
        data = {
            "node_id": "C",
            "graph": self.graph.id
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Node.objects.count(), 3)

    def test_create_edge(self):
        """Test creating an edge between two nodes"""
        url = reverse('edge-list')
        data = {
            "src_node": self.node_a.id,
            "dst_node": self.node_b.id,
            "src_to_dst_data_keys": {"out2": "in2"}
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Edge.objects.count(), 2)

    def test_create_graph(self):
        """Test creating a graph"""
        url = reverse('graph-list')
        data = {
            "name": "New Graph"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Graph.objects.count(), 2)

    def test_graph_retrieve(self):
        """Test retrieving a graph by ID"""
        url = reverse('graph-detail', args=[self.graph.id])
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Test Graph")

    def test_create_runconfig(self):
        """Test creating a run configuration for a graph"""
        url = reverse('runconfig-list')
        data = {
            "graph": self.graph.id,
            "root_inputs": {
                "A": {"input_key": "initial_value"}
            },
            "enable_list": ["A", "B"],
            "data_overwrites": {
                "B": {"overwrite_key": "overwrite_value"}
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RunConfig.objects.count(), 1)

    def test_run_graph(self):
        """Test running a graph and checking data propagation"""
        url = reverse('runconfig-run', args=[self.graph.id])
        data = {
            "root_inputs": {
                "A": {"input_key": "initial_value"}
            },
            "enable_list": ["A", "B"],
            "data_overwrites": {
                "B": {"overwrite_key": "overwrite_value"}
            }
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('run_id', response.data)

    def test_retrieve_node_data_out(self):
        """Test retrieving the output data of a node after run"""
        run_url = reverse('runconfig-run', args=[self.graph.id])
        run_data = {
            "root_inputs": {
                "A": {"input_key": "initial_value"}
            },
            "enable_list": ["A", "B"],
            "data_overwrites": {
                "B": {"overwrite_key": "overwrite_value"}
            }
        }
        run_response = self.client.post(run_url, run_data, format="json")
        run_id = run_response.data['run_id']
        
        node_data_url = reverse('node-data-out', args=[run_id, self.node_a.id])
        response = self.client.get(node_data_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Customize assertions based on expected output structure
