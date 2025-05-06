from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context

from .pod_tools import run_kubectl_command

def register_cluster_tools(mcp: FastMCP):
    """Register all cluster-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_cluster_info(
        output: str = "json"
    ) -> str:
        """Get cluster information"""
        return await run_kubectl_command(
            "cluster-info",
            ["-o", output]
        )

    @mcp.tool()
    async def get_nodes(
        label_selector: Optional[str] = None,
        output: str = "json"
    ) -> str:
        """Get cluster nodes with optional filtering"""
        args = ["nodes"]
        
        if label_selector:
            args.extend(["-l", label_selector])
        
        args.extend(["-o", output])
        return await run_kubectl_command("get", args)

    @mcp.tool()
    async def describe_node(
        node_name: str,
        output: str = "yaml"
    ) -> str:
        """Describe a specific node"""
        return await run_kubectl_command(
            "describe",
            ["node", node_name, "-o", output]
        )

    @mcp.tool()
    async def cordon_node(
        node_name: str
    ) -> str:
        """Mark a node as unschedulable"""
        return await run_kubectl_command(
            "cordon",
            [node_name]
        )

    @mcp.tool()
    async def uncordon_node(
        node_name: str
    ) -> str:
        """Mark a node as schedulable"""
        return await run_kubectl_command(
            "uncordon",
            [node_name]
        )

    @mcp.tool()
    async def drain_node(
        node_name: str,
        force: bool = False,
        ignore_daemonsets: bool = True,
        delete_local_data: bool = False
    ) -> str:
        """Drain a node in preparation for maintenance"""
        args = ["drain", node_name]
        
        if force:
            args.append("--force")
        if ignore_daemonsets:
            args.append("--ignore-daemonsets")
        if delete_local_data:
            args.append("--delete-local-data")
            
        return await run_kubectl_command(*args)

    @mcp.tool()
    async def get_cluster_metrics(
        output: str = "json"
    ) -> str:
        """Get cluster metrics (requires metrics-server)"""
        return await run_kubectl_command(
            "top",
            ["nodes", "-o", output]
        ) 