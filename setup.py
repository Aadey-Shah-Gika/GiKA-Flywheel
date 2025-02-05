from setuptools import setup, find_packages
import os

# Safely read requirements.txt
def read_requirements():
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", encoding="utf-8") as f:
            return f.read().splitlines()
    return []

# Safely read README.md
def read_readme():
    if os.path.exists("README.md"):
        with open("README.md", encoding="utf-8") as f:
            return f.read()
    return "Collecting Relevant Data for your Domain from World Knowledge"

setup(
    name="flywheel",
    version="0.1",
    packages=find_packages(exclude=["tests*"]),  # Exclude test directories
    install_requires=read_requirements(),
    author="GiKA.AI",
    author_email="contact@gikagraph.ai",
    description="Collecting Relevant Data for your Domain from World Knowledge",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/gikagraph-ai/flywheel",  # Replace with the actual GitHub repo
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
