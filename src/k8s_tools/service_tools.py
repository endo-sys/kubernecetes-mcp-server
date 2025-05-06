from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from kubernetes.client import (
    V1Service,
    V1ServiceSpec,
    V1ServicePort,
    V1ObjectMeta
)
from kubernetes.client.rest import ApiException

from .k8s_manager import KubernetesManager
from .service_templates import (
    ServiceType,
    service_templates,
    ServiceConfig,
    PortConfig
)

def register_service_tools(mcp: FastMCP, k8s_manager: KubernetesManager):
    """Register all service-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_services(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """Get services with optional filtering"""
        try:
            if namespace:
                response = k8s_manager.get_core_api().list_namespaced_service(
                    namespace,
                    label_selector=label_selector
                )
            else:
                response = k8s_manager.get_core_api().list_service_for_all_namespaces(
                    label_selector=label_selector
                )
            
            if not response.items:
                return "No services found"
            
            result = []
            for service in response.items:
                result.append(f"Service: {service.metadata.name}")
                result.append(f"Namespace: {service.metadata.namespace}")
                result.append(f"Type: {service.spec.type}")
                result.append("Ports:")
                for port in service.spec.ports:
                    result.append(f"  - {port.port} -> {port.target_port}")
                result.append("-" * 50)
            
            return "\n".join(result)
        except ApiException as e:
            return f"Error getting services: {e}"

    @mcp.tool()
    async def describe_service(
        service_name: str,
        namespace: str
    ) -> str:
        """Describe a specific service"""
        try:
            response = await k8s_manager.get_core_api().read_namespaced_service(
                service_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error describing service: {e}"

    @mcp.tool()
    async def create_service(
        name: str,
        namespace: str,
        service_type: str,
        ports: Optional[List[Dict[str, Any]]] = None,
        selector: Optional[Dict[str, str]] = None,
        custom_config: Optional[ServiceConfig] = None
    ) -> str:
        """Create a new service using a template"""
        try:
            type_enum = ServiceType(service_type)
        except ValueError:
            return f"Invalid service type. Must be one of: {', '.join(t.name for t in ServiceType)}"
        
        template_config = service_templates[type_enum]
        
        # If using custom config, validate and merge
        service_config: Dict[str, Any]
        if custom_config:
            service_config = {
                **template_config,
                **custom_config
            }
        else:
            service_config = {
                **template_config,
                "ports": ports or template_config["ports"],
                "selector": selector or template_config["selector"]
            }
        
        # Create service ports
        service_ports = [
            V1ServicePort(
                port=port["port"],
                target_port=port["targetPort"],
                node_port=port.get("nodePort"),
                protocol=port.get("protocol", "TCP"),
                name=port.get("name")
            )
            for port in service_config["ports"]
        ]
        
        # Create service object
        service = V1Service(
            api_version="v1",
            kind="Service",
            metadata=V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels={
                    "mcp-managed": "true",
                    "app": name
                }
            ),
            spec=V1ServiceSpec(
                type=service_config["type"],
                ports=service_ports,
                selector=service_config["selector"],
                external_ips=service_config.get("externalIPs"),
                load_balancer_ip=service_config.get("loadBalancerIP"),
                session_affinity=service_config.get("sessionAffinity"),
                external_traffic_policy=service_config.get("externalTrafficPolicy")
            )
        )
        
        try:
            response = await k8s_manager.get_core_api().create_namespaced_service(
                namespace,
                service
            )
            k8s_manager.track_resource("Service", name, namespace)
            return str(response)
        except ApiException as e:
            return f"Error creating service: {e}"

    @mcp.tool()
    async def update_service(
        service_name: str,
        namespace: str,
        service_type: Optional[str] = None,
        ports: Optional[List[Dict[str, Any]]] = None,
        selector: Optional[Dict[str, str]] = None
    ) -> str:
        """Update a service's configuration"""
        try:
            patch = {}
            if service_type:
                patch["spec"] = {"type": service_type}
            if ports:
                patch["spec"] = {
                    "ports": [
                        {
                            "port": p["port"],
                            "targetPort": p["targetPort"],
                            "nodePort": p.get("nodePort"),
                            "protocol": p.get("protocol", "TCP"),
                            "name": p.get("name")
                        }
                        for p in ports
                    ]
                }
            if selector:
                patch["spec"] = {"selector": selector}
                
            response = await k8s_manager.get_core_api().patch_namespaced_service(
                service_name,
                namespace,
                patch
            )
            return str(response)
        except ApiException as e:
            return f"Error updating service: {e}"

    @mcp.tool()
    async def delete_service(
        service_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete a service"""
        try:
            response = await k8s_manager.get_core_api().delete_namespaced_service(
                service_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error deleting service: {e}"

    @mcp.tool()
    async def get_service_endpoints(
        service_name: str,
        namespace: str
    ) -> str:
        """Get endpoints for a service"""
        try:
            response = await k8s_manager.get_core_api().read_namespaced_endpoints(
                service_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error getting service endpoints: {e}"

    @mcp.tool()
    async def port_forward_service(
        service_name: str,
        namespace: str,
        local_port: int,
        remote_port: int
    ) -> str:
        """Forward a local port to a service"""
        return await run_kubectl_command(
            "port-forward",
            ["service", service_name, f"{local_port}:{remote_port}", "-n", namespace]
        ) 