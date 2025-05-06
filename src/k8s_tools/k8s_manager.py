from kubernetes import client, config
from kubernetes.client import ApiException
from typing import Dict, Any, Optional
import logging

class KubernetesManager:
    def __init__(self):
        try:
            # Try to load in-cluster config first
            config.load_incluster_config()
        except config.ConfigException:
            try:
                # Fall back to kubeconfig
                config.load_kube_config()
            except config.ConfigException as e:
                raise RuntimeError("Could not configure kubernetes python client") from e
        
        self._tracked_resources: Dict[str, Dict[str, str]] = {}
        
        # Initialize API clients
        self._core_api = client.CoreV1Api()
        self._apps_api = client.AppsV1Api()
        self._batch_api = client.BatchV1Api()
        self._networking_api = client.NetworkingV1Api()
        
    def get_core_api(self) -> client.CoreV1Api:
        return self._core_api
        
    def get_apps_api(self) -> client.AppsV1Api:
        return self._apps_api
        
    def get_batch_api(self) -> client.BatchV1Api:
        return self._batch_api
        
    def get_networking_api(self) -> client.NetworkingV1Api:
        return self._networking_api
        
    def track_resource(self, kind: str, name: str, namespace: str) -> None:
        """Track a resource for cleanup purposes"""
        key = f"{namespace}/{name}"
        self._tracked_resources[key] = {
            "kind": kind,
            "name": name,
            "namespace": namespace
        }
        
    def get_tracked_resources(self) -> Dict[str, Dict[str, str]]:
        return self._tracked_resources
        
    def clear_tracked_resources(self) -> None:
        self._tracked_resources.clear()
        
    async def cleanup_resources(self) -> None:
        """Clean up all tracked resources"""
        for resource in self._tracked_resources.values():
            try:
                if resource["kind"] == "Deployment":
                    self._apps_api.delete_namespaced_deployment(
                        resource["name"],
                        resource["namespace"]
                    )
                elif resource["kind"] == "Service":
                    self._core_api.delete_namespaced_service(
                        resource["name"],
                        resource["namespace"]
                    )
                elif resource["kind"] == "Pod":
                    self._core_api.delete_namespaced_pod(
                        resource["name"],
                        resource["namespace"]
                    )
                elif resource["kind"] == "Job":
                    self._batch_api.delete_namespaced_job(
                        resource["name"],
                        resource["namespace"]
                    )
                elif resource["kind"] == "Ingress":
                    self._networking_api.delete_namespaced_ingress(
                        resource["name"],
                        resource["namespace"]
                    )
            except ApiException as e:
                logging.error(f"Failed to delete resource {resource}: {e}")
                
        self.clear_tracked_resources() 