"""
Pipeline Index Manager for Jarvis-CD.
Manages pipeline indexes stored in repo 'pipelines' directories.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from jarvis_cd.core.config import Jarvis


class PipelineIndexManager:
    """
    Manages pipeline indexes - collections of pipeline scripts stored in repo 'pipelines' directories.
    """

    def __init__(self, jarvis_config: Jarvis):
        """
        Initialize pipeline index manager.

        :param jarvis_config: Jarvis configuration singleton
        """
        self.jarvis_config = jarvis_config
        
    def parse_index_query(self, index_query: str) -> Tuple[str, List[str], str]:
        """
        Parse an index query into repo name, subdirectories, and script name.
        
        :param index_query: Dotted string like 'repo.subdir1.subdir2.script'
        :return: Tuple of (repo_name, subdirs_list, script_name)
        """
        if not index_query or '.' not in index_query:
            raise ValueError(f"Invalid index query: '{index_query}'. Expected format: repo.path.to.script")
            
        parts = index_query.split('.')
        if len(parts) < 2:
            raise ValueError(f"Invalid index query: '{index_query}'. Must have at least repo.script")
            
        repo_name = parts[0]
        script_name = parts[-1]
        subdirs = parts[1:-1]  # Everything between repo and script
        
        return repo_name, subdirs, script_name
        
    def find_repo_path(self, repo_name: str) -> Optional[Path]:
        """
        Find the path to a repository by name.
        
        :param repo_name: Name of the repository
        :return: Path to repository or None if not found
        """
        # Check if it's the builtin repo
        if repo_name == 'builtin':
            return self.jarvis_config.get_builtin_repo_path()
            
        # Search in registered repos
        for repo_path_str in self.jarvis_config.repos['repos']:
            repo_path = Path(repo_path_str)
            if repo_path.name == repo_name and repo_path.exists():
                return repo_path
                
        return None
        
    def find_pipeline_script(self, index_query: str) -> Optional[Path]:
        """
        Find a pipeline script from an index query.
        
        :param index_query: Dotted string like 'repo.subdir1.subdir2.script'
        :return: Path to the script file or None if not found
        """
        repo_name, subdirs, script_name = self.parse_index_query(index_query)
        
        # Find the repository
        repo_path = self.find_repo_path(repo_name)
        if not repo_path:
            return None
            
        # Build path to pipeline index
        pipelines_dir = repo_path / 'pipelines'
        if not pipelines_dir.exists():
            return None
            
        # Build path through subdirectories
        script_dir = pipelines_dir
        for subdir in subdirs:
            script_dir = script_dir / subdir
            if not script_dir.exists():
                return None
                
        # Look for script with .yaml extension
        script_path = script_dir / f'{script_name}.yaml'
        if script_path.exists():
            return script_path
            
        return None
        
    def list_available_scripts(self, repo_name: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
        """
        List all available pipeline scripts in indexes.
        
        :param repo_name: Optional specific repo to list, or None for all repos
        :return: Dictionary mapping repo names to lists of entry dictionaries with 'name' and 'type' keys
        """
        available_scripts = {}
        
        repos_to_check = []
        if repo_name:
            # Check specific repo
            repo_path = self.find_repo_path(repo_name)
            if repo_path:
                repos_to_check.append((repo_name, repo_path))
        else:
            # Check all repos
            # Builtin repo
            builtin_path = self.jarvis_config.get_builtin_repo_path()
            if builtin_path and builtin_path.exists():
                repos_to_check.append(('builtin', builtin_path))
                
            # Registered repos
            for repo_path_str in self.jarvis_config.repos['repos']:
                repo_path = Path(repo_path_str)
                if repo_path.exists():
                    repos_to_check.append((repo_path.name, repo_path))
                    
        # Scan each repo for pipeline scripts
        for repo_name, repo_path in repos_to_check:
            pipelines_dir = repo_path / 'pipelines'
            if not pipelines_dir.exists():
                continue
                
            entries = []
            self._scan_pipeline_directory(pipelines_dir, entries, repo_name)
            
            if entries:
                # Sort by name
                available_scripts[repo_name] = sorted(entries, key=lambda x: x['name'])
                
        return available_scripts
        
    def _scan_pipeline_directory(self, directory: Path, entries: List[Dict[str, str]], repo_name: str, current_path: str = ""):
        """
        Recursively scan a pipeline directory for .yaml files and directories.
        
        :param directory: Directory to scan
        :param entries: List to append found entries to
        :param repo_name: Name of the repository
        :param current_path: Current path within the pipelines directory
        """
        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix == '.yaml':
                    # Build the index query for this script
                    script_name = item.stem  # Remove .yaml extension
                    if current_path:
                        index_query = f"{repo_name}.{current_path}.{script_name}"
                    else:
                        index_query = f"{repo_name}.{script_name}"
                    entries.append({'name': index_query, 'type': 'file'})
                elif item.is_dir():
                    # Add directory entry
                    if current_path:
                        dir_query = f"{repo_name}.{current_path}.{item.name}"
                    else:
                        dir_query = f"{repo_name}.{item.name}"
                    entries.append({'name': dir_query, 'type': 'directory'})
                    
                    # Recursively scan subdirectory
                    if current_path:
                        new_path = f"{current_path}.{item.name}"
                    else:
                        new_path = item.name
                    self._scan_pipeline_directory(item, entries, repo_name, new_path)
        except (OSError, PermissionError):
            # Skip directories we can't read
            pass
            
    def load_pipeline_from_index(self, index_query: str):
        """
        Load a pipeline script from an index directly into the current pipeline.
        
        :param index_query: Dotted string like 'repo.subdir1.subdir2.script'
        """
        script_path = self.find_pipeline_script(index_query)
        if not script_path:
            # List available scripts to help user
            print(f"Pipeline script not found: {index_query}")
            self._print_available_scripts()
            return
            
        # Use Pipeline class to load the script
        from jarvis_cd.core.pipeline import Pipeline
        
        try:
            pipeline = Pipeline()
            pipeline.load('yaml', str(script_path))
            print(f"Loaded pipeline from index: {index_query}")
        except Exception as e:
            print(f"Error loading pipeline from index '{index_query}': {e}")
            
    def copy_pipeline_from_index(self, index_query: str, output_path: Optional[str] = None):
        """
        Copy a pipeline script from an index to a local directory.
        
        :param index_query: Dotted string like 'repo.subdir1.subdir2.script'
        :param output_path: Optional output directory or file path. Defaults to current directory.
        """
        script_path = self.find_pipeline_script(index_query)
        if not script_path:
            # List available scripts to help user
            print(f"Pipeline script not found: {index_query}")
            self._print_available_scripts()
            return
            
        # Determine output path
        if output_path is None:
            # Copy to current directory with same filename
            output_file = Path.cwd() / script_path.name
        else:
            output_path = Path(output_path)
            if output_path.is_dir() or output_path.suffix == '':
                # Output is a directory, use original filename
                output_file = output_path / script_path.name
            else:
                # Output is a specific file
                output_file = output_path
                
        # Create output directory if needed
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(script_path, output_file)
            print(f"Copied pipeline script from '{index_query}' to '{output_file}'")
        except Exception as e:
            print(f"Error copying pipeline script: {e}")
            
    def _print_available_scripts(self):
        """
        Print available pipeline scripts to help user with valid index queries.
        """
        from jarvis_cd.util.logger import logger, Color
        
        available_scripts = self.list_available_scripts()
        
        if not available_scripts:
            print("No pipeline indexes found in any repositories.")
            return
            
        print("Available pipeline scripts:")
        for repo_name, entries in available_scripts.items():
            print(f"  {repo_name}:")
            for entry in entries:
                if entry['type'] == 'file':
                    # Print files in default color
                    print(f"    {entry['name']}")
                elif entry['type'] == 'directory':
                    # Print directories in cyan color
                    logger.print(Color.CYAN, f"    {entry['name']} (directory)")