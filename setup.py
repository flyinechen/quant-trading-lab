#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quantitative Trading Lab
量化交易研究实验室

A comprehensive quantitative trading research and execution platform.
一站式量化研究与交易平台。
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="quant-trading-lab",
    version="0.1.0",
    author="flyinechen",
    author_email="flyinechen@github.com",
    description="📈 量化交易研究实验室 - Quantitative Trading Research Lab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flyinechen/quant-trading-lab",
    packages=find_packages(include=["src", "src.*"]),
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "quant-lab=src.utils.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
