from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from kubernetes.client import (
    V1CronJob,
    V1CronJobSpec,
    V1JobTemplateSpec,
    V1JobSpec,
    V1PodTemplateSpec,
    V1ObjectMeta,
    V1PodSpec,
    V1Container,
    V1ResourceRequirements,
    V1EnvVar,
    V1ContainerPort
)
from kubernetes.client.rest import ApiException

from .k8s_manager import KubernetesManager
from .container_templates import (
    ContainerTemplate,
    container_templates,
    CustomContainerConfig,
    PortConfig,
    EnvVarConfig
)

def register_cronjob_tools(mcp: FastMCP, k8s_manager: KubernetesManager):
    """Register all cronjob-related tools with the MCP server"""
    
    @mcp.tool()
    async def get_cronjobs(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None
    ) -> str:
        """Get cronjobs with optional filtering"""
        try:
            if namespace:
                response = await k8s_manager.get_batch_api().list_namespaced_cron_job(
                    namespace,
                    label_selector=label_selector
                )
            else:
                response = await k8s_manager.get_batch_api().list_cron_job_for_all_namespaces(
                    label_selector=label_selector
                )
            return str(response)
        except ApiException as e:
            return f"Error getting cronjobs: {e}"

    @mcp.tool()
    async def describe_cronjob(
        cronjob_name: str,
        namespace: str
    ) -> str:
        """Describe a specific cronjob"""
        try:
            response = await k8s_manager.get_batch_api().read_namespaced_cron_job(
                cronjob_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error describing cronjob: {e}"

    @mcp.tool()
    async def create_cronjob(
        name: str,
        namespace: str,
        schedule: str,
        template: str,
        completions: int = 1,
        parallelism: int = 1,
        backoff_limit: int = 6,
        custom_config: Optional[CustomContainerConfig] = None
    ) -> str:
        """Create a new cronjob using a template"""
        try:
            template_enum = ContainerTemplate(template)
        except ValueError:
            return f"Invalid template. Must be one of: {', '.join(t.name for t in ContainerTemplate)}"
        
        template_config = container_templates[template_enum]
        
        # If using custom config, validate and merge
        container_config: Dict[str, Any]
        if custom_config:
            container_config = {
                **template_config,
                **custom_config
            }
        else:
            container_config = template_config
        
        # Create container ports
        container_ports = [
            V1ContainerPort(
                container_port=port["containerPort"],
                protocol=port.get("protocol", "TCP"),
                name=port.get("name")
            )
            for port in container_config.get("ports", [])
        ]
        
        # Create environment variables
        env_vars = [
            V1EnvVar(
                name=env["name"],
                value=env.get("value"),
                value_from=env.get("valueFrom")
            )
            for env in container_config.get("env", [])
        ]
        
        # Create resource requirements
        resources = None
        if "resources" in container_config:
            resources = V1ResourceRequirements(
                requests=container_config["resources"].get("requests"),
                limits=container_config["resources"].get("limits")
            )
        
        # Create container
        container = V1Container(
            name=name,
            image=container_config["image"],
            ports=container_ports,
            env=env_vars,
            resources=resources,
            command=container_config.get("command"),
            args=container_config.get("args")
        )
        
        # Create cronjob
        cronjob = V1CronJob(
            api_version="batch/v1",
            kind="CronJob",
            metadata=V1ObjectMeta(
                name=name,
                namespace=namespace,
                labels={
                    "mcp-managed": "true",
                    "app": name
                }
            ),
            spec=V1CronJobSpec(
                schedule=schedule,
                job_template=V1JobTemplateSpec(
                    spec=V1JobSpec(
                        completions=completions,
                        parallelism=parallelism,
                        backoff_limit=backoff_limit,
                        template=V1PodTemplateSpec(
                            metadata=V1ObjectMeta(
                                labels={"app": name}
                            ),
                            spec=V1PodSpec(
                                containers=[container],
                                restart_policy="OnFailure"
                            )
                        )
                    )
                )
            )
        )
        
        try:
            response = await k8s_manager.get_batch_api().create_namespaced_cron_job(
                namespace,
                cronjob
            )
            k8s_manager.track_resource("CronJob", name, namespace)
            return str(response)
        except ApiException as e:
            return f"Error creating cronjob: {e}"

    @mcp.tool()
    async def delete_cronjob(
        cronjob_name: str,
        namespace: str,
        force: bool = False
    ) -> str:
        """Delete a cronjob"""
        try:
            response = await k8s_manager.get_batch_api().delete_namespaced_cron_job(
                cronjob_name,
                namespace
            )
            return str(response)
        except ApiException as e:
            return f"Error deleting cronjob: {e}"

    @mcp.tool()
    async def get_cronjob_logs(
        cronjob_name: str,
        namespace: str,
        container: Optional[str] = None,
        follow: bool = False,
        tail_lines: Optional[int] = None
    ) -> str:
        """Get logs from a cronjob's jobs"""
        try:
            # First get the cronjob to find its jobs
            cronjob = await k8s_manager.get_batch_api().read_namespaced_cron_job(
                cronjob_name,
                namespace
            )
            
            # Get jobs for this cronjob
            jobs = await k8s_manager.get_batch_api().list_namespaced_job(
                namespace,
                label_selector=f"job-name={cronjob_name}"
            )
            
            # Get logs from each job's pods
            logs = []
            for job in jobs.items:
                pods = await k8s_manager.get_core_api().list_namespaced_pod(
                    namespace,
                    label_selector=f"job-name={job.metadata.name}"
                )
                
                for pod in pods.items:
                    pod_logs = await k8s_manager.get_core_api().read_namespaced_pod_log(
                        pod.metadata.name,
                        namespace,
                        container=container,
                        follow=follow,
                        tail_lines=tail_lines
                    )
                    logs.append(f"=== Logs from pod {pod.metadata.name} in job {job.metadata.name} ===\n{pod_logs}")
            
            return "\n".join(logs)
        except ApiException as e:
            return f"Error getting cronjob logs: {e}" 