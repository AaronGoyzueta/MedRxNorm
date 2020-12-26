import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

project_urls = {
  'GitHub Link': 'https://github.com/AaronGoyzueta/MedRxNorm'
}

setuptools.setup(
    name="MedRxNorm",
    version="0.0.4",
    author="Aaron Goyzueta",
    author_email="aarongoyzueta@gmail.com",
    description="Python module for normalizing medical prescriptions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=["pynini", "num2words", "textblob", "text2digits"],
    project_urls=project_urls
)