import asyncio
from mcp.server.fastmcp import FastMCP
from k8s_tools.k8s_manager import KubernetesManager
from k8s_tools.deployment_tools import register_deployment_tools
from k8s_tools.service_tools import register_service_tools
from k8s_tools.pod_tools import register_pod_tools
from k8s_tools.job_tools import register_job_tools
from k8s_tools.cronjob_tools import register_cronjob_tools
from k8s_tools.ingress_tools import register_ingress_tools
from k8s_tools.yaml_tools import apply_yaml
from k8s_tools.helm_tools import register_helm_tools
from typing import Optional

def main():
    # Initialize the MCP server
    mcp = FastMCP("k8s-server")
    
    # Initialize Kubernetes manager
    k8s_manager = KubernetesManager()
    
    # Register all Kubernetes tools
    register_deployment_tools(mcp, k8s_manager)
    register_service_tools(mcp, k8s_manager)
    register_pod_tools(mcp, k8s_manager)
    register_job_tools(mcp, k8s_manager)
    register_cronjob_tools(mcp, k8s_manager)
    register_ingress_tools(mcp, k8s_manager)
    
    # Register Helm tools
    register_helm_tools(mcp)
    
    # Register YAML tool
    @mcp.tool()
    async def apply_yaml_tool(
        yaml_content: str,
        namespace: Optional[str] = None,
        force: bool = False
    ) -> str:
        """Apply YAML content to the Kubernetes cluster"""
        return await apply_yaml(yaml_content, namespace, force)
    
    # Start the server
    mcp.run()

if __name__ == "__main__":
    main() 