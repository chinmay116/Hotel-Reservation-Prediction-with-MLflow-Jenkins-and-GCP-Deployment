from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name = "ML-OPS_Project_1",
    version = "0.1.0",
    author = "Chinmay",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=requirements,
    include_package_data=True,  # Include non-Python files from MANIFEST.in if needed
    zip_safe=False
)