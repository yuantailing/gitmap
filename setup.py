import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as reqs_file:
    requirements = reqs_file.read().splitlines()

setuptools.setup(
    name="gitmap",
    version="0.0.1",
    author="Tailing Yuan",
    author_email="yuantailing@gmail.com",
    description="GitMap: Map git commits to new commits, preserving history.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yuantailing/gitmap",
    packages=["gitmap"],
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.4',
)
