import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

short_description = "An unofficial Bullhorn REST API client written in Python."

setuptools.setup(
    name="pyhorn-flow",
    version="1.1.0",
    author="Stephan Chang",
    author_email="stephan.chang@flowef.com",
    description=short_description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/flowef/pyhorn/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
