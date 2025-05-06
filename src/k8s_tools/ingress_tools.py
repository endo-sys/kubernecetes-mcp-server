from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from kubernetes.client import (
    V1Ingress,
    V1IngressSpec,
    V1IngressRule,
    V1HTTPIngressRuleValue,
    V1HTTPIngressPath,
    V1IngressBackend,
    V1ObjectMeta
)
from kubernetes.client.api.networking_v1_api import NetworkingV1Api
from kubernetes.client.rest import ApiException

from .k8s_manager import KubernetesManager

def register_ingress_tools(mcp: FastMCP, k8s_manager: KubernetesManager):
    """Register all ingress-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_ingresses(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """Get ingresses with optional filtering"""
        try:
            if namespace:
                response = await k8s_manager.get_networking_api().list_namespaced_ingress(
                    namespace,
                    label_selector=label_selector
                )
            else:
                response = await k8s_manager.get_networking_api().list_ingress_for_all_namespaces(
                    label_selector=label_selector
                )
            return str(response)
        except ApiException as e:
            return f"Error getting ingresses: {e}"

    @mcp.tool()
    async def describe_ingress(
        ingress_name: str,
        namespace: str
    ) -> str:
        """Describe a specific ingress"""
        try:
            response = await k8s_manager.get_networking_api().read_namespaced_ingress(
                ingress_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error describing ingress: {e}"

    @mcp.tool()
    async def create_ingress(
        name: str,
        namespace: str,
        rules: List[Dict[str, Any]],
        tls: Optional[List[Dict[str, Any]]] = None,
        annotations: Optional[Dict[str, str]] = None
    ) -> str:
        """Create a new ingress"""
        # Create ingress rules
        ingress_rules = []
        for rule in rules:
            paths = []
            for path in rule.get("paths", []):
                paths.append(
                    V1HTTPIngressPath(
                        path=path.get("path", "/"),
                        path_type=path.get("pathType", "Prefix"),
                        backend=V1IngressBackend(
                            service=V1IngressBackend(
                                name=path["service"]["name"],
                                port=V1IngressBackend(
                                    number=path["service"]["port"]
                                )
                            )
                        )
                    )
                )
            
            ingress_rules.append(
                V1IngressRule(
                    host=rule.get("host"),
                    http=V1HTTPIngressRuleValue(
                        paths=paths
                    )
                )
            )
        
        # Create TLS configuration
        ingress_tls = None
        if tls:
            ingress_tls = [
                {
                    "hosts": tls_config.get("hosts", []),
                    "secretName": tls_config.get("secretName")
                }
                for tls_config in tls
            ]
        
        # Create ingress
        ingress = V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels={
                    "mcp-managed": "true",
                    "app": name
                },
                annotations=annotations or {}
            ),
            spec=V1IngressSpec(
                rules=ingress_rules,
                tls=ingress_tls
            )
        )
        
        try:
            response = await k8s_manager.get_networking_api().create_namespaced_ingress(
                namespace,
                ingress
            )
            k8s_manager.track_resource("Ingress", name, namespace)
            return str(response)
        except ApiException as e:
            return f"Error creating ingress: {e}"

    @mcp.tool()
    async def update_ingress(
        ingress_name: str,
        namespace: str,
        rules: Optional[List[Dict[str, Any]]] = None,
        tls: Optional[List[Dict[str, Any]]] = None,
        annotations: Optional[Dict[str, str]] = None
    ) -> str:
        """Update an ingress's configuration"""
        try:
            patch = {}
            if rules:
                patch["spec"] = {"rules": rules}
            if tls:
                patch["spec"] = {"tls": tls}
            if annotations:
                patch["metadata"] = {"annotations": annotations}
                
            response = await k8s_manager.get_networking_api().patch_namespaced_ingress(
                ingress_name,
                namespace,
                patch
            )
            return str(response)
        except ApiException as e:
            return f"Error updating ingress: {e}"

    @mcp.tool()
    async def delete_ingress(
        ingress_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete an ingress"""
        try:
            response = await k8s_manager.get_networking_api().delete_namespaced_ingress(
                ingress_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error deleting ingress: {e}" 