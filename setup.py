#!/usr/bin/env python3
"""
Setup script for Afiliados AI Agent.
Instalación: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="afiliados-ai-agent",
    version="1.0.0",
    description="🤖 Asistente estratégico de marketing de afiliados en Grupos de Facebook + Hotmart",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Afiliados AI Agent",
    url="https://github.com/afiliados-ai-agent",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "requests>=2.31.0",
        "schedule>=1.2.0",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "afiliados=run:main",
            "afiliados-scheduler=automation.scheduler:main",
            "afiliados-reporter=automation.reporter:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Spanish",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business :: Marketing",
    ],
    keywords="afiliados, hotmart, facebook, marketing, ventas, whatsapp",
    project_urls={
        "Source": "https://github.com/afiliados-ai-agent",
        "Video Estrategia": "https://www.youtube.com/watch?v=mdQkdvi3BUg",
    },
)
