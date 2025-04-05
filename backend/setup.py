from setuptools import setup, find_packages

setup(
    name="newsletter-builder",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "openai",
        "python-dotenv",
    ],
) 