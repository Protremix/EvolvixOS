from setuptools import setup, find_packages

setup(
    name="evolvixos",
    version="1.0.0",
    description="Python SDK for EvolvixOS — self-hostable AI engineering platform",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="EvolvixOS",
    license="MIT",
    url="https://github.com/Protremix/EvolvixOS",
    packages=find_packages(),
    install_requires=["requests>=2.28"],
    python_requires=">=3.8",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
)
