# KiwiQ AI

A Django-based web application with REST API support.

## Features

- Built with Django 5.1.2 and Django REST Framework 3.15.2
- PostgreSQL database support
- Docker and Docker Compose configuration for easy deployment
- Poetry for dependency management

## Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional)
- Poetry (optional)

## Installation

### Using Docker (Recommended)

1. Clone the repository:



```bash
git clone [<repository-url>](https://github.com/mr-195/KIWIQ.AI_Assignment.git)
cd KIWIQ.AI_Assignment 
```

## 2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate 
On Windows: venv\Scripts\activate
```


## 3. Install dependencies:

```bash
pip install -r requirements.txt
```

# Running the Algorithm

To execute the main algorithm with tests:

```bash
python Algorithm/main.py
```

## FOR BACKEND ASSIGNMENT in Django and Django Rest Framework

## Configuration
<!-- You can skip this (only needed for external database connections) -->
1. Create a `.env` file in the root directory:
```
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
```

## Running the Application

To start the backend server:
```bash
python main.py
```

The server will start running at `http://localhost:8000` by default.

<!-- Using curl  -->
Create node A
```bash
curl -X POST http://localhost:8000/api/nodes/ -H "Content-Type: application/json" -d '{
    "node_id": "A",
    "data_out": {
        "out1": 42
    }
}'
```

Create node B
```bash
curl -X POST http://localhost:8000/api/nodes/ -H "Content-Type: application/json" -d '{
    "node_id": "B",
    "data_out": {
        "out2": 84
    }
}'
```

Create node C
```bash
curl -X POST http://localhost:8000/api/nodes/ -H "Content-Type: application/json" -d '{
    "node_id": "C"
}'
```

Create edge A to B
```bash
curl -X POST http://localhost:8000/api/nodes/ -H "Content-Type: application/json" -d '{
    "node_id": "C"
}'
```


Create edge B to C

```bash
curl -X POST http://localhost:8000/api/edges/ -H "Content-Type: application/json" -d '{
    "src_node": 2,  // Use Node B ID
    "dst_node": 3,  // Use Node C ID
    "src_to_dst_data_keys": {
        "out2": "in2"
    }
}'
```

Create Graph
```bash
curl -X POST http://localhost:8000/api/graphs/ -H "Content-Type: application/json" -d '{
    "nodes": [1, 2, 3],  // Use IDs from node creation responses
    "edges": [1, 2]      // Use IDs from edge creation responses
}'
```

Run config

```bash
curl -X POST http://localhost:8000/api/runs/ -H "Content-Type: application/json" -d '{
    "graph": 1,  // Use the ID from the graph creation response
    "root_inputs": {
        "A": {
            "out1": 42
        }
    },
    "data_overwrites": {
        "B": {
            "out2": 84
        }
    },
    "enable_list": ["A", "B"],
    "disable_list": []
}'
```
You can get the list of nodes and edges with all the informations, by making a GET request to /api/nodes and /api/edges respectively
For getting something using node_id, /api/nodes/node_id -> Supports all CRUD operations
For getting something using edge_id, /api/edge/edge_id -> Supports all CRUD operations

Examples:
```bash
    curl -X GET http://localhost:8000/api/nodes/1/
    curl -X GET http://localhost:8000/api/nodes/2/
    curl -X GET http://localhost:8000/api/nodes/3/
```
