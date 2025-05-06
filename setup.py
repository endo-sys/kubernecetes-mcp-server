from setuptools import setup, find_packages

setup(
    name="k8s-mcp-server",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp[cli]>=0.4.0",
        "kubernetes>=29.0.0",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.7",
    author="Enes Erdoğan",
    author_email="enes70442@@gmail.com",
    description="A Kubernetes MCP server for natural language interaction with Kubernetes clusters",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/endo-sys/kubernecetes-mcp-server.git",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "k8s-mcp-server=k8s_mcp_server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "k8s_tools": ["*.py"],
    },
) 