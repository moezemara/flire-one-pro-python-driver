"""Setup configuration for FLIR One Python library."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="flir-one-python",
    version="1.0.0",
    author="FLIR One Python Contributors",
    description="Python library for FLIR One Pro Gen-3 thermal camera",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/flir-one-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: System :: Hardware :: Universal Serial Bus (USB)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "opencv-python>=4.5.0",
        "libusb1>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
            "mypy>=0.900",
        ],
    },
    entry_points={
        "console_scripts": [
            "flir-one=flir_one.cli:main",
        ],
    },
    package_data={
        "flir_one": [
            "palettes/*.raw",
        ],
    },
    include_package_data=True,
    keywords="flir thermal camera lepton usb imaging",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/flir-one-python/issues",
        "Source": "https://github.com/yourusername/flir-one-python",
    },
)
