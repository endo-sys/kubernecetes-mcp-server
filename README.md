# Kubernetes MCP Server

This is a Model Context Protocol (MCP) server that provides comprehensive Kubernetes functionality through the MCP Python SDK. It allows you to interact with your Kubernetes cluster using natural language through an MCP client.

## Features

The server provides a wide range of Kubernetes operations organized into logical modules:

### Pod Operations
- Get pods with filtering and output format options
- Describe specific pods
- Get pod logs with various options
- Execute commands in pods
- Get pod metrics

### Deployment Operations
- Get deployments with filtering and output format options
- Describe specific deployments
- Scale deployments
- Manage deployment rollouts (status, history, restart, undo)
- Get deployment metrics

### Service Operations
- Get services with filtering and output format options
- Describe specific services
- Expose deployments as services
- Port forward to services

### Namespace Operations
- Get namespaces with filtering
- Describe specific namespaces
- Create and delete namespaces
- Get namespace resource quotas

### Cluster Operations
- Get cluster information
- Get and describe nodes
- Manage node scheduling (cordon/uncordon)
- Drain nodes for maintenance
- Get cluster metrics

## Prerequisites

- Python 3.7+
- kubectl installed and configured
- Access to a Kubernetes cluster
- MCP client (e.g., Claude Desktop)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Server

1. Development mode with MCP Inspector:
   ```bash
   python -m mcp.inspector src/k8s_mcp_server.py
   ```

2. Install in Claude Desktop:
   ```bash
   python -m mcp.install src/k8s_mcp_server.py
   ```

3. Run directly:
   ```bash
   python src/k8s_mcp_server.py
   ```

### Using the Tools

Once connected through an MCP client, you can use natural language to interact with your Kubernetes cluster. For example:

- "Get all pods in the default namespace"
- "Describe the deployment named 'nginx' in the 'web' namespace"
- "Get logs from the 'frontend' pod in the 'production' namespace"
- "Scale the 'backend' deployment to 3 replicas"
- "Create a new namespace called 'staging' with label environment=staging"

## Project Structure

```
src/
├── k8s_mcp_server.py      # Main server entry point
├── k8s_tools/            # Tool modules
│   ├── __init__.py
│   ├── pod_tools.py      # Pod-related tools
│   ├── deployment_tools.py # Deployment-related tools
│   ├── service_tools.py  # Service-related tools
│   ├── namespace_tools.py # Namespace-related tools
│   └── cluster_tools.py  # Cluster-related tools
└── requirements.txt      # Project dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 