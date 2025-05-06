import yaml
from typing import Optional
from kubernetes.client.rest import ApiException
from kubernetes.client import ApiClient

from .k8s_manager import KubernetesManager

async def apply_yaml(
    yaml_content: str,
    namespace: Optional[str] = None,
    force: bool = False
) -> str:
    """Apply YAML content to the Kubernetes cluster
    
    Args:
        yaml_content: The YAML content to apply
        namespace: Optional namespace to apply the YAML in
        force: Whether to force the apply operation
        
    Returns:
        str: The result of the apply operation
    """
    try:
        # Parse the YAML content
        resources = yaml.safe_load_all(yaml_content)
        
        results = []
        for resource in resources:
            if not resource:
                continue
                
            # Get the appropriate API client based on the resource type
            api_client = None
            if resource["kind"] == "ConfigMap":
                api_client = KubernetesManager().get_core_api()
                if namespace:
                    resource["metadata"]["namespace"] = namespace
                try:
                    # Try to get the existing resource
                    existing = api_client.read_namespaced_config_map(
                        resource["metadata"]["name"],
                        resource["metadata"]["namespace"]
                    )
                    # Update if exists
                    response = api_client.replace_namespaced_config_map(
                        resource["metadata"]["name"],
                        resource["metadata"]["namespace"],
                        resource
                    )
                    results.append(f"ConfigMap {resource['metadata']['name']} updated successfully")
                except ApiException as e:
                    if e.status == 404:
                        # Create if doesn't exist
                        response = api_client.create_namespaced_config_map(
                            resource["metadata"]["namespace"],
                            resource
                        )
                        results.append(f"ConfigMap {resource['metadata']['name']} created successfully")
                    else:
                        raise e
            else:
                results.append(f"Unsupported resource kind: {resource['kind']}")
                
        return "\n".join(results)
    except Exception as e:
        return f"Error applying YAML: {str(e)}" 