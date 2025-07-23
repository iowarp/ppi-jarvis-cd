import setuptools
import os
import sys 
import shutil
import sysconfig
from pathlib import Path


ret = setuptools.setup(
    name="jarvis_cd",
    packages=setuptools.find_packages(),
    scripts=['bin/jarvis', 'bin/jarvis-completion-helper'],
    version="0.0.1",
    author="Luke Logan",
    author_email="llogan@hawk.iit.edu",
    description="Create basic for applications",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/scs-lab/jarvis-cd",
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 0 - Pre-Alpha",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: None",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Application Configuration",
    ],
    install_requires=[
        'pandas',
        'pyyaml'
    ],
    data_files=[
        ('share/bash-completion/completions', ['completion/jarvis-completion.bash']),
    ],
)

# Install the builtin directory to ~/.jarvis
project_dir = os.path.dirname(os.path.realpath(__file__))
local_builtin_path = os.path.join(project_dir, 'builtin')
install_builtin_path = os.path.join(Path.home(), '.jarvis', 'builtin')  
if not os.path.exists(os.path.dirname(install_builtin_path)):
    os.makedirs(os.path.dirname(install_builtin_path))
shutil.copytree(local_builtin_path, install_builtin_path, dirs_exist_ok=True)
