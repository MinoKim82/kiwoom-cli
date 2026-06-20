from setuptools import setup, find_packages

setup(
    name="kiwoom-cli",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "requests",
        "click",
    ],
    extras_require={
        "dev": ["pytest", "requests-mock"],
    },
    entry_points={
        "console_scripts": [
            "kiwoom=kiwoom.cli:main",
        ],
    },
)
