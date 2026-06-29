from vehicle_import.vehicle_import.strategies.equal import EqualAllocationStrategy


class AllocationEngine:

    def allocate(self, cost_entry, vins):

        strategy = EqualAllocationStrategy()

        return strategy.allocate(cost_entry, vins)