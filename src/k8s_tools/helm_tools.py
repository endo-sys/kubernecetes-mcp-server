import asyncio
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from kubernetes.client.rest import ApiException

async def run_helm_command(command: str, args: List[str] = None) -> str:
    """Run a Helm command and return its output"""
    try:
        cmd = ["helm", command]
        if args:
            cmd.extend(args)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return f"Error: {stderr.decode()}"
        
        return stdout.decode()
    except Exception as e:
        return f"Error executing Helm command: {str(e)}"

def register_helm_tools(mcp: FastMCP):
    """Register all Helm-related tools with the MCP server"""
    
    @mcp.tool()
    async def helm_repo_add(
        name: str,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        force_update: bool = False
    ) -> str:
        """
        Add a Helm repository.
        
        Args:
            name: Name of the repository
            url: URL of the repository
            username: Optional username for authentication
            password: Optional password for authentication
            force_update: Whether to force update the repository
            
        Returns:
            Status of the repository addition
        """
        args = [name, url]
        
        if username and password:
            args.extend(["--username", username, "--password", password])
        if force_update:
            args.append("--force-update")
            
        return await run_helm_command("repo", ["add"] + args)

    @mcp.tool()
    async def helm_show_values(
        chart: str,
        version: Optional[str] = None,
        repo: Optional[str] = None
    ) -> str:
        """
        Show the values.yaml file for a Helm chart.
        
        Args:
            chart: The name of the chart (e.g., 'nginx' or 'bitnami/nginx')
            version: Optional chart version to show values for
            repo: Optional repository URL to fetch the chart from
            
        Returns:
            The contents of the values.yaml file for the specified chart
        """
        args = []
        if version:
            args.extend(["--version", version])
        if repo:
            args.extend(["--repo", repo])
        args.append(chart)
        
        return await run_helm_command("show", ["values"] + args)

    @mcp.tool()
    async def helm_install(
        release_name: str,
        chart: str,
        namespace: str,
        values: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        repo: Optional[str] = None,
        create_namespace: bool = True,
        wait: bool = True,
        timeout: Optional[str] = None
    ) -> str:
        """
        Install a Helm chart.
        
        Args:
            release_name: Name of the release
            chart: The name of the chart (e.g., 'nginx' or 'bitnami/nginx')
            namespace: Namespace to install the release in
            values: Optional dictionary of values to override
            version: Optional chart version to install
            repo: Optional repository URL to fetch the chart from
            create_namespace: Whether to create the namespace if it doesn't exist
            wait: Whether to wait for the release to be ready
            timeout: Optional timeout for the installation
            
        Returns:
            Status of the installation
        """
        args = [
            release_name,
            chart,
            "--namespace", namespace
        ]
        
        if values:
            # Create a temporary values file
            import tempfile
            import yaml
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(values, f)
                args.extend(["-f", f.name])
        
        if version:
            args.extend(["--version", version])
        if repo:
            args.extend(["--repo", repo])
        if create_namespace:
            args.append("--create-namespace")
        if wait:
            args.append("--wait")
        if timeout:
            args.extend(["--timeout", timeout])
        
        return await run_helm_command("install", args)

    @mcp.tool()
    async def helm_upgrade(
        release_name: str,
        chart: str,
        namespace: str,
        values: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        repo: Optional[str] = None,
        wait: bool = True,
        timeout: Optional[str] = None,
        force: bool = False,
        reset_values: bool = False
    ) -> str:
        """
        Upgrade a Helm release.
        
        Args:
            release_name: Name of the release to upgrade
            chart: The name of the chart (e.g., 'nginx' or 'bitnami/nginx')
            namespace: Namespace where the release is installed
            values: Optional dictionary of values to override
            version: Optional chart version to upgrade to
            repo: Optional repository URL to fetch the chart from
            wait: Whether to wait for the upgrade to complete
            timeout: Optional timeout for the upgrade
            force: Whether to force resource updates through a replacement strategy
            reset_values: Whether to reset the values to the ones built into the chart
            
        Returns:
            Status of the upgrade
        """
        args = [
            release_name,
            chart,
            "--namespace", namespace
        ]
        
        if values:
            # Create a temporary values file
            import tempfile
            import yaml
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(values, f)
                args.extend(["-f", f.name])
        
        if version:
            args.extend(["--version", version])
        if repo:
            args.extend(["--repo", repo])
        if wait:
            args.append("--wait")
        if timeout:
            args.extend(["--timeout", timeout])
        if force:
            args.append("--force")
        if reset_values:
            args.append("--reset-values")
        
        return await run_helm_command("upgrade", args) 