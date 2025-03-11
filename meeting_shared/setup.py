"""
Setup script for the meeting_shared package.
"""

from setuptools import setup, find_packages

setup(
    name="meeting_shared",
    version="0.1.0",
    description="Shared utilities for Meeting App microservices",
    author="Meeting App Team",
    packages=find_packages(),
    install_requires=[
        "flask>=2.0.0",
        "sqlalchemy>=1.4.0",
        "requests>=2.25.0",
        "pydantic>=2.0.0",
        "redis>=4.0.0",
        "PyJWT>=2.0.0",
        "hvac>=1.0.0",  # For Vault integration
        "kubernetes>=20.0.0",  # For Kubernetes integration
        "PyYAML>=6.0.0",  # For YAML config support
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'isort>=5.0.0',
            'flake8>=4.0.0',
        ]
    },
    python_requires='>=3.9',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
) 