from abc import ABC, abstractmethod


class AllocationStrategy(ABC):

    @abstractmethod
    def allocate(self, cost_entry, vins):
        """Return ledger rows."""
        pass