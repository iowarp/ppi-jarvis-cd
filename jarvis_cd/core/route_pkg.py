"""
Base classes for routed application deployment.
Provides routing functionality that delegates lifecycle methods to implementation-specific subclasses.
"""
from .pkg import Application, Service
from typing import Dict, Any, List


class RouteApp(Application):
    """
    Base class for routed application deployment.

    This class provides automatic delegation of lifecycle methods (start, stop, status, kill, clean)
    to implementation-specific subclasses based on the deploy mode configuration.

    Subclasses should:
    1. Override _configure_menu() to define package-specific parameters
    2. Override _get_deploy_mode() if custom deploy mode mapping is needed
    3. Implement specific deployment classes (e.g., MyAppDefault, MyAppContainer)
    """

    def _configure_menu(self) -> List[Dict[str, Any]]:
        """
        Get the configuration menu for deploy parameters.

        :return: List of configuration option dictionaries
        """
        return []

    def _get_deploy_mode(self) -> str:
        """
        Get the deploy mode from pipeline or config and map it to delegate class name.
        Pipeline deploy_mode takes precedence over package config.
        Subclasses can override this to provide custom mapping logic.

        :return: Deploy mode string (e.g., 'default', 'container')
        """
        # Check pipeline deploy_mode first
        if hasattr(self.pipeline, 'deploy_mode') and self.pipeline.deploy_mode:
            deploy_mode = self.pipeline.deploy_mode
        else:
            # Fall back to package config
            deploy_mode = self.config.get('deploy_mode', 'default')

        return deploy_mode

    def _configure(self, **kwargs):
        """
        Configure the appropriate implementation via delegation.

        :param kwargs: Configuration parameters
        :return: None
        """
        # Call parent to set config
        super()._configure(**kwargs)

        # Delegate to appropriate implementation
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)
        delegate._configure(**kwargs)

    def start(self):
        """
        Start the application using the appropriate implementation.

        :return: None
        """
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)
        delegate.start()

    def stop(self):
        """
        Stop the application using the appropriate implementation.

        :return: None
        """
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)
        delegate.stop()

    def status(self):
        """
        Get status of the application using the appropriate implementation.

        :return: Status information
        """
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)
        return delegate.status()

    def kill(self):
        """
        Kill the application using the appropriate implementation.

        :return: None
        """
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)
        delegate.kill()

    def clean(self):
        """
        Clean application data using the appropriate implementation.

        :return: None
        """
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)
        delegate.clean()

    def augment_container(self) -> str:
        """
        Generate Dockerfile commands to install this package in a container.
        Delegates to the appropriate implementation based on deploy mode.

        :return: Dockerfile commands as a string
        """
        deploy_mode = self._get_deploy_mode()
        delegate = self._get_delegate(deploy_mode)

        # Check if delegate has augment_container method
        if hasattr(delegate, 'augment_container'):
            return delegate.augment_container()
        else:
            # Fall back to base implementation
            return super().augment_container()


class RouteService(RouteApp):
    """
    Alias for RouteApp following service naming conventions.

    This class is identical to RouteApp but follows the naming convention
    where long-running applications are called "services".
    """
    pass
