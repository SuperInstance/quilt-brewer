from setuptools import setup, find_packages

setup(
    name="quilt-brewer",
    version="0.1.0",
    description="Recipe-driven walker factory — grow substrate walkers from JSON recipes.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="SuperInstance",
    author_email="casey@superinstance.dev",
    url="https://github.com/SuperInstance/quilt-brewer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
