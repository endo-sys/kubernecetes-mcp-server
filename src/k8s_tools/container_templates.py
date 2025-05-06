from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional

class ContainerTemplate(Enum):
    NGINX = "nginx"
    NODEJS = "nodejs"
    PYTHON = "python"
    CUSTOM = "custom"

class ResourceConfig(TypedDict, total=False):
    requests: Dict[str, str]
    limits: Dict[str, str]

class PortConfig(TypedDict, total=False):
    containerPort: int
    protocol: str
    name: str

class EnvVarConfig(TypedDict, total=False):
    name: str
    value: str
    valueFrom: Dict[str, Any]

class VolumeMountConfig(TypedDict, total=False):
    name: str
    mountPath: str
    readOnly: bool

class CustomContainerConfig(TypedDict, total=False):
    image: str
    ports: List[PortConfig]
    resources: ResourceConfig
    env: List[EnvVarConfig]
    command: List[str]
    args: List[str]
    volumeMounts: List[VolumeMountConfig]

# Base templates for different container types
container_templates: Dict[ContainerTemplate, CustomContainerConfig] = {
    ContainerTemplate.NGINX: {
        "image": "nginx:latest",
        "ports": [{"containerPort": 80, "protocol": "TCP", "name": "http"}],
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"}
        }
    },
    ContainerTemplate.NODEJS: {
        "image": "node:18",
        "ports": [{"containerPort": 3000, "protocol": "TCP", "name": "http"}],
        "resources": {
            "requests": {"cpu": "200m", "memory": "256Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"}
        }
    },
    ContainerTemplate.PYTHON: {
        "image": "python:3.9",
        "ports": [{"containerPort": 8000, "protocol": "TCP", "name": "http"}],
        "resources": {
            "requests": {"cpu": "200m", "memory": "256Mi"},
            "limits": {"cpu": "1000m", "memory": "1Gi"}
        }
    },
    ContainerTemplate.CUSTOM: {
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"}
        }
    }
} 