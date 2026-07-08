from .allocation_context import AllocationContext
from .ledger_builder import LedgerBuilder
from .strategy_factory import StrategyFactory


class AllocationEngine:

    def rebuild(
        self,
        cost_entry,
    ):

        context = AllocationContext(
            cost_entry,
        )

        strategy = (
            StrategyFactory()
            .create(context)
        )

        result = strategy.allocate(
            context,
        )

        rows = LedgerBuilder().build(
            context,
            result,
        )

        return rows