from setuptools import find_packages, setup

setup(
    name="mcqgenerator",
    version="0.0.1",
    author="gunjan barke",
    author_email="gunjan11barke@gmail.com",
    description="Automated MCQ Generator using LangChain + Groq API",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-groq",
        "langchain-community",
        "langchain-core",
        "streamlit",
        "pypdf",
        "python-dotenv",
    ]
)