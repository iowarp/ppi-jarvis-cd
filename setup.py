import setuptools
import os
import sys 
import shutil
import sysconfig
from pathlib import Path
from setuptools.command.install import install
from setuptools.command.develop import develop


# Use setup() with minimal configuration since pyproject.toml handles most metadata
setuptools.setup(
    scripts=['bin/jarvis', 'bin/jarvis-install-builtin'],
)
