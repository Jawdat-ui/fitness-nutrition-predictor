"""Setup script for Fitness & Nutrition Predictor."""

from setuptools import setup, find_packages

setup(
    name="fitness-nutrition-predictor",
    version="1.0.0",
    description="Track nutrition and predict strength/training metrics",
    author="Your Name",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0,<3.0",
        "matplotlib>=3.7",
        "tabulate>=0.9",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "fitness-predictor=main:main",
        ],
    },
)
