from abc import ABC, abstractmethod

class AlertObserver(ABC):
    """
    Abstract base class for alert observers.
    Concrete observers should implement the `notify` method.
    """

    @abstractmethod
    def notify(self, alert_instance):
        """
        Notify the observer with the alert instance.
        """
        pass
