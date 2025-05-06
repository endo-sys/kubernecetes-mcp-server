from enum import Enum
from typing import Dict, Any, List, Optional, TypedDict

class ContainerTemplate(str, Enum):
    """Available container templates"""
    NGINX = "NGINX"
    REDIS = "REDIS"
    POSTGRES = "POSTGRES"
    MYSQL = "MYSQL"
    CUSTOM = "CUSTOM"

class PortConfig(TypedDict, total=False):
    """Port configuration for containers"""
    containerPort: int
    protocol: str
    name: str

class EnvVarConfig(TypedDict, total=False):
    """Environment variable configuration"""
    name: str
    value: Optional[str]
    valueFrom: Optional[Dict[str, Any]]

class ContainerConfig(TypedDict, total=False):
    """Container configuration"""
    image: str
    ports: List[PortConfig]
    env: List[EnvVarConfig]
    resources: Dict[str, Dict[str, str]]
    command: Optional[List[str]]
    args: Optional[List[str]]

class PodConfig(TypedDict, total=False):
    """Pod configuration"""
    image: str
    ports: List[PortConfig]
    env: List[EnvVarConfig]
    resources: Dict[str, Dict[str, str]]
    command: Optional[List[str]]
    args: Optional[List[str]]
    restartPolicy: str

# Template configurations for different container types
pod_templates: Dict[ContainerTemplate, PodConfig] = {
    ContainerTemplate.NGINX: {
        "image": "nginx:latest",
        "ports": [
            {
                "containerPort": 80,
                "protocol": "TCP",
                "name": "http"
            }
        ],
        "resources": {
            "requests": {
                "cpu": "100m",
                "memory": "128Mi"
            },
            "limits": {
                "cpu": "500m",
                "memory": "512Mi"
            }
        },
        "restartPolicy": "Always"
    },
    ContainerTemplate.REDIS: {
        "image": "redis:latest",
        "ports": [
            {
                "containerPort": 6379,
                "protocol": "TCP",
                "name": "redis"
            }
        ],
        "resources": {
            "requests": {
                "cpu": "100m",
                "memory": "128Mi"
            },
            "limits": {
                "cpu": "500m",
                "memory": "512Mi"
            }
        },
        "restartPolicy": "Always"
    },
    ContainerTemplate.POSTGRES: {
        "image": "postgres:latest",
        "ports": [
            {
                "containerPort": 5432,
                "protocol": "TCP",
                "name": "postgres"
            }
        ],
        "env": [
            {
                "name": "POSTGRES_PASSWORD",
                "value": "postgres"
            }
        ],
        "resources": {
            "requests": {
                "cpu": "200m",
                "memory": "256Mi"
            },
            "limits": {
                "cpu": "1000m",
                "memory": "1Gi"
            }
        },
        "restartPolicy": "Always"
    },
    ContainerTemplate.MYSQL: {
        "image": "mysql:latest",
        "ports": [
            {
                "containerPort": 3306,
                "protocol": "TCP",
                "name": "mysql"
            }
        ],
        "env": [
            {
                "name": "MYSQL_ROOT_PASSWORD",
                "value": "mysql"
            }
        ],
        "resources": {
            "requests": {
                "cpu": "200m",
                "memory": "256Mi"
            },
            "limits": {
                "cpu": "1000m",
                "memory": "1Gi"
            }
        },
        "restartPolicy": "Always"
    },
    ContainerTemplate.CUSTOM: {
        "image": "",
        "ports": [],
        "env": [],
        "resources": {
            "requests": {
                "cpu": "100m",
                "memory": "128Mi"
            },
            "limits": {
                "cpu": "500m",
                "memory": "512Mi"
            }
        },
        "restartPolicy": "Always"
    }
} 