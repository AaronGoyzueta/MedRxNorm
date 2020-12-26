import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="MedRxNorm",
    version="0.0.1",
    author="Aaron Goyzueta",
    author_email="aarongoyzueta@gmail.com",
    description="Python module for normalizing medical prescriptions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages()
)