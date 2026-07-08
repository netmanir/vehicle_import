class AllocationResult:

    def __init__(self):

        self.rows = []


    def add_row(
        self,

        vehicle,

        currency,
        foreign_amount,

        base_currency,
        base_amount,

        remark=None,
    ):

        self.rows.append({

            "vehicle":
                vehicle,

            "currency":
                currency,

            "foreign_amount":
                foreign_amount,

            "base_currency":
                base_currency,

            "base_amount":
                base_amount,

            "remark":
                remark,
        })