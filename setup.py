from setuptools import setup, find_packages

setup(
    name="travel_router",
    version="0.1.0",
    # packages=find_packages(),
    # package_dir={"":"."},
    packages=[
        "feature",
        "feature.trip",
        "feature.sql",
        "feature.retrieval",
        "feature.llm",
        "feature.line",
        "feature.nosql",
        "main",
        "main.main_trip",
        "main.main_plan",
    ],
    install_requires=[
        "googlemaps",
        "pandas",
        "pydantic",
        "requests",
        "python-dotenv",
        "openai==0.28",
        "qdrant-client",
        "pytest",
    ],
    python_requires=">=3.12",
)
