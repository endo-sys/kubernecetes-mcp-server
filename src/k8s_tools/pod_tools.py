import asyncio
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from kubernetes.client import (
    V1Pod,
    V1PodSpec,
    V1Container,
    V1ResourceRequirements,
    V1EnvVar,
    V1ContainerPort,
    V1ObjectMeta
)
from kubernetes.client.rest import ApiException

from .k8s_manager import KubernetesManager
from .pod_templates import (
    ContainerTemplate,
    pod_templates,
    PodConfig,
    ContainerConfig
)

async def run_kubectl_command(command: str, args: List[str] = None) -> str:
    """Run a kubectl command and return its output"""
    try:
        cmd = ["kubectl", command]
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
        return f"Error executing kubectl command: {str(e)}"

def format_pod_info(pod: V1Pod) -> str:
    """Format pod information into a readable string"""
    status = pod.status
    spec = pod.spec
    metadata = pod.metadata
    
    info = [
        f"Pod: {metadata.name}",
        f"Namespace: {metadata.namespace}",
        f"Status: {status.phase}",
        f"Node: {status.host_ip}",
        f"IP: {status.pod_ip}",
        "\nContainers:"
    ]
    
    for container in spec.containers:
        info.append(f"  - {container.name}")
        info.append(f"    Image: {container.image}")
        if container.ports:
            info.append("    Ports:")
            for port in container.ports:
                info.append(f"      - {port.container_port}/{port.protocol}")
    
    return "\n".join(info)

def register_pod_tools(mcp: FastMCP, k8s_manager: KubernetesManager):
    """Register all pod-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_pods(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """Get pods with optional filtering"""
        try:
            api = k8s_manager.get_core_api()
            if namespace:
                response = api.list_namespaced_pod(
                    namespace,
                    label_selector=label_selector
                )
            else:
                response = api.list_pod_for_all_namespaces(
                    label_selector=label_selector
                )
            
            if not response.items:
                return "No pods found"
            
            result = []
            for pod in response.items:
                result.append(format_pod_info(pod))
                result.append("-" * 50)
            
            return "\n".join(result)
        except ApiException as e:
            return f"Error getting pods: {e}"

    @mcp.tool()
    async def describe_pod(
        pod_name: str,
        namespace: str
    ) -> str:
        """Describe a specific pod"""
        try:
            api = k8s_manager.get_core_api()
            response = api.read_namespaced_pod(
                pod_name,
                namespace
            )
            return format_pod_info(response)
        except ApiException as e:
            return f"Error describing pod: {e}"

    @mcp.tool()
    async def create_pod(
        name: str,
        namespace: str,
        template: str,
        custom_config: Optional[PodConfig] = None
    ) -> str:
        """Create a new pod using a template"""
        try:
            template_enum = ContainerTemplate(template)
        except ValueError:
            return f"Invalid template. Must be one of: {', '.join(t.name for t in ContainerTemplate)}"
        
        template_config = pod_templates[template_enum]
        
        # If using custom config, validate and merge
        pod_config: Dict[str, Any]
        if custom_config:
            pod_config = {
                **template_config,
                **custom_config
            }
        else:
            pod_config = template_config
        
        # Create container ports
        container_ports = [
            V1ContainerPort(
                container_port=port["containerPort"],
                protocol=port.get("protocol", "TCP"),
                name=port.get("name")
            )
            for port in pod_config.get("ports", [])
        ]
        
        # Create environment variables
        env_vars = [
            V1EnvVar(
                name=env["name"],
                value=env.get("value"),
                value_from=env.get("valueFrom")
            )
            for env in pod_config.get("env", [])
        ]
        
        # Create resource requirements
        resources = None
        if pod_config.get("resources"):
            resources = V1ResourceRequirements(
                requests=pod_config["resources"].get("requests"),
                limits=pod_config["resources"].get("limits")
            )
        
        # Create container
        container = V1Container(
            name=name,
            image=pod_config["image"],
            ports=container_ports,
            env=env_vars,
            resources=resources,
            command=pod_config.get("command"),
            args=pod_config.get("args")
        )
        
        # Create pod
        pod = V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels={
                    "mcp-managed": "true",
                    "app": name
                }
            ),
            spec=V1PodSpec(
                containers=[container],
                restart_policy=pod_config.get("restartPolicy", "Always")
            )
        )
        
        try:
            api = k8s_manager.get_core_api()
            response = api.create_namespaced_pod(
                namespace,
                pod
            )
            k8s_manager.track_resource("Pod", name, namespace)
            return f"Pod created successfully:\n{format_pod_info(response)}"
        except ApiException as e:
            return f"Error creating pod: {e}"

    @mcp.tool()
    async def delete_pod(
        pod_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete a pod"""
        try:
            api = k8s_manager.get_core_api()
            response = api.delete_namespaced_pod(
                pod_name,
                namespace
            )
            return f"Pod {pod_name} deleted successfully"
        except ApiException as e:
            return f"Error deleting pod: {e}"

    @mcp.tool()
    async def get_pod_logs(
        pod_name: str,
        namespace: str,
        container: Optional[str] = None,
        follow: bool = False,
        tail_lines: Optional[int] = None
    ) -> str:
        """Get logs from a pod"""
        try:
            api = k8s_manager.get_core_api()
            response = api.read_namespaced_pod_log(
                pod_name,
                namespace,
                container=container,
                follow=follow,
                tail_lines=tail_lines
            )
            return f"Logs for pod {pod_name}:\n{response}"
        except ApiException as e:
            return f"Error getting pod logs: {e}"

    @mcp.tool()
    async def exec_pod_command(
        pod_name: str,
        namespace: str,
        command: List[str],
        container: Optional[str] = None
    ) -> str:
        """Execute a command in a pod"""
        try:
            # Build the kubectl command
            cmd = ["kubectl", "exec", pod_name, "-n", namespace]
            if container:
                cmd.extend(["-c", container])
            cmd.extend(["--"] + command)
            
            # Execute the command
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
            return f"Error executing command in pod: {e}"

    @mcp.tool()
    async def get_pod_metrics(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """Get pod metrics (requires metrics-server)"""
        args = ["top", "pods"]
        if namespace:
            args.extend(["-n", namespace])
        else:
            args.append("--all-namespaces")
            
        if label_selector:
            args.extend(["-l", label_selector])
            
        return await run_kubectl_command(*args) 