"""
Setup script for DB-GPT
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="db-gpt",
    version="0.1.0",
    author="DB-GPT Team",
    author_email="team@db-gpt.com",
    description="BabyAGI with Database Integration for LLM-driven analytics",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/makalin/db-gpt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "local": [
            "ctransformers>=0.2.0",
            "sentence-transformers>=2.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "db-gpt=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 