import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis_cd.core.config import JarvisConfig, load_class
from jarvis_cd.util.argparse import ArgParse


class PackageManager:
    """
    Manages individual Jarvis packages - configuration and lifecycle.
    """
    
    def __init__(self, jarvis_config: JarvisConfig):
        """
        Initialize package manager.
        
        :param jarvis_config: Jarvis configuration manager
        """
        self.jarvis_config = jarvis_config
        
    def configure_package(self, package_spec: str, config_args: Dict[str, Any]):
        """
        Configure a package with given arguments.
        
        :param package_spec: Package specification (pkg or pipeline.pkg)
        :param config_args: Configuration arguments
        """
        # Parse package specification
        if '.' in package_spec:
            # pipeline.pkg format
            pipeline_name, pkg_id = package_spec.split('.', 1)
            
            # Load pipeline to get package info
            pipeline_dir = self.jarvis_config.get_pipeline_dir(pipeline_name)
            if not pipeline_dir.exists():
                raise ValueError(f"Pipeline not found: {pipeline_name}")
                
            config_file = pipeline_dir / 'pipeline.yaml'
            with open(config_file, 'r') as f:
                pipeline_config = yaml.safe_load(f)
                
            # Find package in pipeline
            pkg_def = None
            for pkg in pipeline_config['packages']:
                if pkg['pkg_id'] == pkg_id:
                    pkg_def = pkg
                    break
                    
            if not pkg_def:
                raise ValueError(f"Package not found in pipeline {pipeline_name}: {pkg_id}")
                
        else:
            # Just package name - assume current pipeline
            current_pipeline_dir = self.jarvis_config.get_current_pipeline_dir()
            if not current_pipeline_dir:
                raise ValueError("No current pipeline. Specify as pipeline.pkg or create a pipeline first.")
                
            config_file = current_pipeline_dir / 'pipeline.yaml'
            with open(config_file, 'r') as f:
                pipeline_config = yaml.safe_load(f)
                
            # Find package in current pipeline
            pkg_def = None
            for pkg in pipeline_config['packages']:
                if pkg['pkg_id'] == package_spec:
                    pkg_def = pkg
                    break
                    
            if not pkg_def:
                raise ValueError(f"Package not found in current pipeline: {package_spec}")
                
            pipeline_name = pipeline_config['name']
            pkg_id = package_spec
            
        # Load package class to get configuration menu
        pkg_instance = self._load_package_instance(pkg_def)
        
        # Get configuration menu if available
        config_menu = []
        if hasattr(pkg_instance, '_configure_menu'):
            config_menu = pkg_instance._configure_menu()
            
        # Create a temporary argument parser for this package's configuration
        config_parser = PackageConfigParser(pkg_id, config_menu)
        config_parser.define_options()
        
        # Convert config_args dict to argument list
        arg_list = []
        for key, value in config_args.items():
            arg_list.extend([f'--{key}={value}'])
            
        # Parse configuration arguments
        try:
            parsed_config = config_parser.parse(arg_list)
        except Exception as e:
            print(f"Configuration error: {e}")
            print(f"Available options for {pkg_id}:")
            for option in config_menu:
                aliases = f" (aliases: {', '.join(option.get('aliases', []))})" if option.get('aliases') else ""
                print(f"  --{option['name']}: {option.get('msg', 'No description')}{aliases}")
            return
            
        # Apply configuration to package instance
        if hasattr(pkg_instance, 'configure'):
            try:
                pkg_instance.configure(**config_parser.kwargs)
                print(f"Configured package {pkg_id} successfully")
            except Exception as e:
                print(f"Error configuring package {pkg_id}: {e}")
        else:
            print(f"Package {pkg_id} has no configure method")
            
        # Update package configuration in pipeline
        pkg_def['config'].update(config_parser.kwargs)
        
        # Save updated pipeline configuration
        pipeline_dir = self.jarvis_config.get_pipeline_dir(pipeline_name)
        config_file = pipeline_dir / 'pipeline.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(pipeline_config, f, default_flow_style=False)
            
        print(f"Saved configuration for {package_spec}")
        
    def list_package_config(self, package_spec: str):
        """
        List configuration options for a package.
        
        :param package_spec: Package specification
        """
        # Parse package specification similar to configure_package
        # This is a simplified version for listing config options
        
        # Try to find package class
        if '.' in package_spec:
            pkg_type = package_spec
        else:
            pkg_type = self.jarvis_config.find_package(package_spec)
            if not pkg_type:
                print(f"Package not found: {package_spec}")
                return
                
        # Load package class
        try:
            pkg_instance = self._load_package_by_type(pkg_type)
            
            if hasattr(pkg_instance, '_configure_menu'):
                config_menu = pkg_instance._configure_menu()
                
                print(f"Configuration options for {package_spec}:")
                for option in config_menu:
                    name = option['name']
                    msg = option.get('msg', 'No description')
                    type_name = option.get('type', str).__name__
                    default = option.get('default', 'None')
                    required = option.get('required', False)
                    aliases = option.get('aliases', [])
                    
                    req_str = " (required)" if required else ""
                    alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
                    
                    print(f"  --{name} <{type_name}>: {msg}{req_str}{alias_str}")
                    print(f"    Default: {default}")
                    
            else:
                print(f"Package {package_spec} has no configuration options")
                
        except Exception as e:
            print(f"Error loading package {package_spec}: {e}")
            
    def _load_package_instance(self, pkg_def: Dict[str, Any]):
        """
        Load a package instance from package definition.
        
        :param pkg_def: Package definition dictionary
        :return: Package instance
        """
        pkg_type = pkg_def['pkg_type']
        return self._load_package_by_type(pkg_type)
        
    def _load_package_by_type(self, pkg_type: str):
        """
        Load a package instance by package type.
        
        :param pkg_type: Package type string
        :return: Package instance
        """
        # Find package class
        if '.' in pkg_type:
            # Full specification like "builtin.ior"
            import_parts = pkg_type.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
        else:
            # Just package name, search in repos
            full_spec = self.jarvis_config.find_package(pkg_type)
            if not full_spec:
                raise ValueError(f"Package not found: {pkg_type}")
            import_parts = full_spec.split('.')
            repo_name = import_parts[0]
            pkg_name = import_parts[1]
            
        # Determine class name (capitalize first letter)
        class_name = pkg_name.capitalize()
        
        # Load class
        if repo_name == 'builtin':
            repo_path = str(self.jarvis_config.get_builtin_repo_path())
        else:
            # Find repo path in registered repos
            repo_path = None
            for registered_repo in self.jarvis_config.repos['repos']:
                if Path(registered_repo).name == repo_name:
                    repo_path = registered_repo
                    break
                    
            if not repo_path:
                raise ValueError(f"Repository not found: {repo_name}")
                
        import_str = f"{repo_name}.{pkg_name}.package"
        pkg_class = load_class(import_str, repo_path, class_name)
        
        if not pkg_class:
            raise ValueError(f"Package class not found: {class_name} in {import_str}")
            
        # Create instance
        pkg_instance = pkg_class()
        
        return pkg_instance


class PackageConfigParser(ArgParse):
    """
    Argument parser for package configuration options.
    """
    
    def __init__(self, package_name: str, config_menu: List[Dict[str, Any]]):
        """
        Initialize package configuration parser.
        
        :param package_name: Name of the package
        :param config_menu: Configuration menu from package
        """
        super().__init__()
        self.package_name = package_name
        self.config_menu = config_menu
        
    def define_options(self):
        """Define configuration options based on package's _configure_menu"""
        
        # Add main configuration command
        self.add_menu('')
        self.add_cmd('', keep_remainder=True)
        
        # Convert package config menu to ArgParse format
        args_list = []
        for option in self.config_menu:
            arg_def = {
                'name': option['name'],
                'msg': option.get('msg', f"Configuration option: {option['name']}"),
                'type': option.get('type', str),
                'default': option.get('default'),
                'required': option.get('required', False)
            }
            
            # Add aliases if present
            if 'aliases' in option:
                arg_def['aliases'] = option['aliases']
                
            # Add choices if present
            if 'choices' in option:
                arg_def['choices'] = option['choices']
                
            args_list.append(arg_def)
            
        if args_list:
            self.add_args(args_list)
            
    def main_menu(self):
        """Handle main configuration command"""
        pass  # Configuration is handled by the caller