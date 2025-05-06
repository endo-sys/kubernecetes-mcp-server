from enum import Enum
from typing import TypedDict, List, Dict, Any, Optional

class ServiceType(Enum):
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"

class PortConfig(TypedDict, total=False):
    port: int
    targetPort: int
    nodePort: Optional[int]
    protocol: str
    name: str

class ServiceConfig(TypedDict, total=False):
    type: str
    ports: List[PortConfig]
    selector: Dict[str, str]
    externalIPs: List[str]
    loadBalancerIP: Optional[str]
    sessionAffinity: str
    externalTrafficPolicy: str

# Base templates for different service types
service_templates: Dict[ServiceType, ServiceConfig] = {
    ServiceType.CLUSTER_IP: {
        "type": "ClusterIP",
        "ports": [{"port": 80, "targetPort": 80, "protocol": "TCP", "name": "http"}],
        "selector": {},
        "sessionAffinity": "None"
    },
    ServiceType.NODE_PORT: {
        "type": "NodePort",
        "ports": [{"port": 80, "targetPort": 80, "nodePort": 30000, "protocol": "TCP", "name": "http"}],
        "selector": {},
        "sessionAffinity": "None"
    },
    ServiceType.LOAD_BALANCER: {
        "type": "LoadBalancer",
        "ports": [{"port": 80, "targetPort": 80, "protocol": "TCP", "name": "http"}],
        "selector": {},
        "sessionAffinity": "None",
        "externalTrafficPolicy": "Cluster"
    },
    ServiceType.EXTERNAL_NAME: {
        "type": "ExternalName",
        "externalName": "",
        "ports": [{"port": 80, "protocol": "TCP", "name": "http"}]
    }
} 