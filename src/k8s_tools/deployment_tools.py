from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from kubernetes.client import (
    V1Deployment,
    V1DeploymentSpec,
    V1PodTemplateSpec,
    V1PodSpec,
    V1Container,
    V1ResourceRequirements,
    V1EnvVar,
    V1ContainerPort,
    V1ObjectMeta,
    V1LabelSelector,
    V1Service,
    V1ServiceSpec,
    V1ServicePort
)
from kubernetes.client.rest import ApiException
import asyncio

from .k8s_manager import KubernetesManager

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

def format_deployment_info(deployment: V1Deployment) -> str:
    """Format deployment information into a readable string"""
    spec = deployment.spec
    status = deployment.status
    metadata = deployment.metadata
    
    info = [
        f"Deployment: {metadata.name}",
        f"Namespace: {metadata.namespace}",
        f"Replicas: {spec.replicas} (Desired) / {status.available_replicas} (Available)",
        f"Strategy: {spec.strategy.type}",
        "\nContainers:"
    ]
    
    for container in spec.template.spec.containers:
        info.append(f"  - {container.name}")
        info.append(f"    Image: {container.image}")
        if container.ports:
            info.append("    Ports:")
            for port in container.ports:
                info.append(f"      - {port.container_port}/{port.protocol}")
        if container.env:
            info.append("    Environment:")
            for env in container.env:
                info.append(f"      - {env.name}={env.value}")
    
    return "\n".join(info)

def register_deployment_tools(mcp: FastMCP, k8s_manager: KubernetesManager):
    """Register all deployment-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_deployments(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """Get deployments with optional filtering"""
        try:
            api = k8s_manager.get_apps_api()
            if namespace:
                response = api.list_namespaced_deployment(
                    namespace,
                    label_selector=label_selector
                )
            else:
                response = api.list_deployment_for_all_namespaces(
                    label_selector=label_selector
                )
            
            if not response.items:
                return "No deployments found"
            
            result = []
            for deployment in response.items:
                result.append(format_deployment_info(deployment))
                result.append("-" * 50)
            
            return "\n".join(result)
        except ApiException as e:
            return f"Error getting deployments: {e}"

    @mcp.tool()
    async def describe_deployment(
        deployment_name: str,
        namespace: str
    ) -> str:
        """Describe a specific deployment"""
        try:
            api = k8s_manager.get_apps_api()
            response = api.read_namespaced_deployment(
                deployment_name,
                namespace
            )
            return format_deployment_info(response)
        except ApiException as e:
            return f"Error describing deployment: {e}"

    @mcp.tool()
    async def create_deployment(
        name: str,
        namespace: str,
        image: str,
        replicas: int = 1,
        ports: Optional[List[Dict[str, Any]]] = None,
        env: Optional[List[Dict[str, Any]]] = None,
        resources: Optional[Dict[str, Dict[str, str]]] = None
    ) -> str:
        """Create a new deployment with the specified configuration"""
        # Create container ports
        container_ports = []
        if ports:
            container_ports = [
                V1ContainerPort(
                    container_port=port["containerPort"],
                    protocol=port.get("protocol", "TCP"),
                    name=port.get("name")
                )
                for port in ports
            ]
        
        # Create environment variables
        env_vars = []
        if env:
            env_vars = [
                V1EnvVar(
                    name=env_var["name"],
                    value=env_var.get("value"),
                    value_from=env_var.get("valueFrom")
                )
                for env_var in env
            ]
        
        # Create resource requirements
        container_resources = None
        if resources:
            container_resources = V1ResourceRequirements(
                requests=resources.get("requests"),
                limits=resources.get("limits")
            )
        
        # Create container
        container = V1Container(
            name=name,
            image=image,
            ports=container_ports,
            env=env_vars,
            resources=container_resources
        )
        
        # Create deployment
        deployment = V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels={
                    "mcp-managed": "true",
                    "app": name
                }
            ),
            spec=V1DeploymentSpec(
                replicas=replicas,
                selector=V1LabelSelector(
                    match_labels={
                        "app": name
                    }
                ),
                template=V1PodTemplateSpec(
                    metadata=V1ObjectMeta(
                        labels={
                            "app": name
                        }
                    ),
                    spec=V1PodSpec(
                        containers=[container],
                        restart_policy="Always"
                    )
                )
            )
        )
        
        try:
            api = k8s_manager.get_apps_api()
            response = api.create_namespaced_deployment(
                namespace,
                deployment
            )
            k8s_manager.track_resource("Deployment", name, namespace)
            return f"Deployment created successfully:\n{format_deployment_info(response)}"
        except ApiException as e:
            return f"Error creating deployment: {e}"

    @mcp.tool()
    async def delete_deployment(
        deployment_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete a deployment"""
        try:
            api = k8s_manager.get_apps_api()
            response = api.delete_namespaced_deployment(
                deployment_name,
                namespace
            )
            return f"Deployment {deployment_name} deleted successfully"
        except ApiException as e:
            return f"Error deleting deployment: {e}"

    @mcp.tool()
    async def scale_deployment(
        deployment_name: str,
        namespace: str,
        replicas: int
    ) -> str:
        """Scale a deployment to a specific number of replicas"""
        try:
            api = k8s_manager.get_apps_api()
            response = api.patch_namespaced_deployment_scale(
                deployment_name,
                namespace,
                {"spec": {"replicas": replicas}}
            )
            return f"Deployment {deployment_name} scaled to {replicas} replicas"
        except ApiException as e:
            return f"Error scaling deployment: {e}"

    @mcp.tool()
    async def rollout_deployment(
        deployment_name: str,
        namespace: str,
        action: str
    ) -> str:
        """Manage deployment rollouts"""
        valid_actions = ["status", "history", "restart", "undo"]
        if action not in valid_actions:
            return f"Invalid action. Must be one of: {', '.join(valid_actions)}"
        
        try:
            if action == "restart":
                response = await k8s_manager.get_apps_api().patch_namespaced_deployment(
                    deployment_name,
                    namespace,
                    {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": "now"}}}}}
                )
            elif action == "undo":
                response = await k8s_manager.get_apps_api().patch_namespaced_deployment(
                    deployment_name,
                    namespace,
                    {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": "now"}}}}}
                )
            else:
                response = await k8s_manager.get_apps_api().read_namespaced_deployment(
                    deployment_name,
                    namespace
                )
            return str(response)
        except ApiException as e:
            return f"Error performing rollout action: {e}"

    @mcp.tool()
    async def update_deployment(
        deployment_name: str,
        namespace: str,
        image: Optional[str] = None,
        replicas: Optional[int] = None,
        env: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Update a deployment's configuration"""
        try:
            patch = {}
            if image:
                patch["spec"] = {"template": {"spec": {"containers": [{"name": deployment_name, "image": image}]}}}
            if replicas is not None:
                patch["spec"] = {"replicas": replicas}
            if env:
                patch["spec"] = {
                    "template": {
                        "spec": {
                            "containers": [{
                                "name": deployment_name,
                                "env": [{"name": e["name"], "value": e["value"]} for e in env]
                            }]
                        }
                    }
                }
                
            api = k8s_manager.get_apps_api()
            response = api.patch_namespaced_deployment(
                deployment_name,
                namespace,
                patch
            )
            return f"Deployment updated successfully:\n{format_deployment_info(response)}"
        except ApiException as e:
            return f"Error updating deployment: {e}"

    @mcp.tool()
    async def get_deployment_metrics(
        deployment_name: str,
        namespace: str
    ) -> str:
        """Get metrics for a deployment"""
        try:
            response = await k8s_manager.get_custom_objects_api().get_namespaced_custom_object(
                "metrics.k8s.io",
                "v1beta1",
                namespace,
                "deployments",
                deployment_name
            )
            return str(response)
        except ApiException as e:
            return f"Error getting deployment metrics: {e}"

    @mcp.tool()
    async def expose_deployment(
        deployment_name: str,
        namespace: str,
        port: int,
        target_port: Optional[int] = None,
        service_type: str = "ClusterIP"
    ) -> str:
        """Expose a deployment as a service"""
        try:
            # Create service
            service = V1Service(
                api_version="v1",
                kind="Service",
                metadata=V1ObjectMeta(
                    name=deployment_name,
                    namespace=namespace,
                    labels={
                        "mcp-managed": "true",
                        "app": deployment_name
                    }
                ),
                spec=V1ServiceSpec(
                    selector={
                        "app": deployment_name
                    },
                    ports=[
                        V1ServicePort(
                            port=port,
                            target_port=target_port or port,
                            protocol="TCP"
                        )
                    ],
                    type=service_type
                )
            )
            
            # Create the service
            api = k8s_manager.get_core_api()
            response = api.create_namespaced_service(
                namespace,
                service
            )
            
            k8s_manager.track_resource("Service", deployment_name, namespace)
            
            # Get the service details
            service_info = []
            service_info.append(f"Service: {response.metadata.name}")
            service_info.append(f"Namespace: {response.metadata.namespace}")
            service_info.append(f"Type: {response.spec.type}")
            service_info.append("Ports:")
            for port in response.spec.ports:
                service_info.append(f"  - {port.port} -> {port.target_port}")
            
            if response.spec.type == "LoadBalancer":
                # Wait for LoadBalancer IP
                while True:
                    service = api.read_namespaced_service(
                        deployment_name,
                        namespace
                    )
                    if service.status.load_balancer.ingress:
                        service_info.append(f"External IP: {service.status.load_balancer.ingress[0].ip}")
                        break
                    await asyncio.sleep(1)
            
            return "Service created successfully:\n" + "\n".join(service_info)
        except ApiException as e:
            return f"Error exposing deployment: {e}" 