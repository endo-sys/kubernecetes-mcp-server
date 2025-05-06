from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context

from .pod_tools import run_kubectl_command

def register_statefulset_tools(mcp: FastMCP):
    """Register all statefulset and replica set related tools with the MCP server"""
    
    @mcp.tool()
    async def get_statefulsets(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
        output: str = "json"
    ) -> str:
        """Get statefulsets with optional filtering and output format"""
        args = ["statefulsets"]
        if namespace:
            args.extend(["-n", namespace])
        else:
            args.append("--all-namespaces")
        
        if label_selector:
            args.extend(["-l", label_selector])
        
        args.extend(["-o", output])
        return await run_kubectl_command("get", args)

    @mcp.tool()
    async def describe_statefulset(
        statefulset_name: str,
        namespace: str,
        output: str = "yaml"
    ) -> str:
        """Describe a specific statefulset"""
        return await run_kubectl_command(
            "describe",
            ["statefulset", statefulset_name, "-n", namespace, "-o", output]
        )

    @mcp.tool()
    async def create_statefulset(
        name: str,
        namespace: str,
        image: str,
        replicas: int = 1,
        labels: Optional[Dict[str, str]] = None,
        service_name: Optional[str] = None,
        volume_claim_templates: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Create a new statefulset"""
        args = ["create", "statefulset", name, "-n", namespace]
        
        if image:
            args.extend(["--image", image])
        if replicas:
            args.extend(["--replicas", str(replicas)])
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in labels.items())
            args.extend(["--labels", label_str])
        if service_name:
            args.extend(["--service-name", service_name])
            
        return await run_kubectl_command(*args)

    @mcp.tool()
    async def scale_statefulset(
        statefulset_name: str,
        namespace: str,
        replicas: int
    ) -> str:
        """Scale a statefulset to a specific number of replicas"""
        return await run_kubectl_command(
            "scale",
            ["statefulset", statefulset_name, "-n", namespace, f"--replicas={replicas}"]
        )

    @mcp.tool()
    async def delete_statefulset(
        statefulset_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete a statefulset"""
        args = ["delete", "statefulset", statefulset_name, "-n", namespace]
        
        if force:
            args.append("--force")
            
        return await run_kubectl_command(*args)

    @mcp.tool()
    async def get_replicasets(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
        output: str = "json"
    ) -> str:
        """Get replicasets with optional filtering and output format"""
        args = ["replicasets"]
        if namespace:
            args.extend(["-n", namespace])
        else:
            args.append("--all-namespaces")
        
        if label_selector:
            args.extend(["-l", label_selector])
        
        args.extend(["-o", output])
        return await run_kubectl_command("get", args)

    @mcp.tool()
    async def describe_replicaset(
        replicaset_name: str,
        namespace: str,
        output: str = "yaml"
    ) -> str:
        """Describe a specific replicaset"""
        return await run_kubectl_command(
            "describe",
            ["replicaset", replicaset_name, "-n", namespace, "-o", output]
        )

    @mcp.tool()
    async def scale_replicaset(
        replicaset_name: str,
        namespace: str,
        replicas: int
    ) -> str:
        """Scale a replicaset to a specific number of replicas"""
        return await run_kubectl_command(
            "scale",
            ["replicaset", replicaset_name, "-n", namespace, f"--replicas={replicas}"]
        )

    @mcp.tool()
    async def delete_replicaset(
        replicaset_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete a replicaset"""
        args = ["delete", "replicaset", replicaset_name, "-n", namespace]
        
        if force:
            args.append("--force")
            
        return await run_kubectl_command(*args) 