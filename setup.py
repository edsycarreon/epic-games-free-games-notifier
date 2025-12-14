"""Setup configuration for Epic Games Free Games Notifier."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="epic-games-free-games-notifier",
    version="1.0.0",
    author="Your Name",
    description="Fetch and notify about free games from Epic Games Store",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "requests>=2.31.0",
        "PyYAML>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.7.1",
            "types-requests>=2.31.0",
            "types-PyYAML>=6.0.12",
        ],
    },
    entry_points={
        "console_scripts": [
            "epic-games-notifier=src.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
