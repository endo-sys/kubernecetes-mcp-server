from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context

from .pod_tools import run_kubectl_command

def register_namespace_tools(mcp: FastMCP):
    """Register all namespace-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_namespaces(
        label_selector: Optional[str] = None,
        output: str = "json"
    ) -> str:
        """Get all namespaces with optional filtering"""
        args = ["namespaces"]
        
        if label_selector:
            args.extend(["-l", label_selector])
        
        args.extend(["-o", output])
        return await run_kubectl_command("get", args)

    @mcp.tool()
    async def describe_namespace(
        namespace: str,
        output: str = "yaml"
    ) -> str:
        """Describe a specific namespace"""
        return await run_kubectl_command(
            "describe",
            ["namespace", namespace, "-o", output]
        )

    @mcp.tool()
    async def create_namespace(
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a new namespace"""
        args = ["create", "namespace", name]
        
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in labels.items())
            args.extend(["--labels", label_str])
            
        return await run_kubectl_command(*args)

    @mcp.tool()
    async def delete_namespace(
        name: str,
        force: bool = False
    ) -> str:
        """Delete a namespace"""
        args = ["delete", "namespace", name]
        
        if force:
            args.append("--force")
            
        return await run_kubectl_command(*args)

    @mcp.tool()
    async def get_namespace_quota(
        namespace: str,
        output: str = "json"
    ) -> str:
        """Get resource quota for a namespace"""
        return await run_kubectl_command(
            "get",
            ["quota", "-n", namespace, "-o", output]
        ) 