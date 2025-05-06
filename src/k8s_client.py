import asyncio
from mcp.client import Client
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

async def main():
    # Create a client
    client = Client("k8s-client")
    
    # Connect to the server
    async with AsyncExitStack() as stack:
        # Connect to the server using stdio
        transport = await stack.enter_async_context(
            stdio_client({
                "command": "python",
                "args": ["src/k8s_mcp_server.py"]
            })
        )
        
        # Initialize the client session
        session = await stack.enter_async_context(
            client.session(transport)
        )
        
        # List available tools
        tools = await session.list_tools()
        print("Available tools:", [tool.name for tool in tools])
        
        # Example: Create a deployment
        response = await session.call_tool(
            "create_deployment",
            {
                "name": "nginx-deployment",
                "namespace": "default",
                "template": "NGINX",
                "replicas": 2
            }
        )
        print("Deployment created:", response)

if __name__ == "__main__":
    asyncio.run(main()) 