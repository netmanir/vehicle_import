class LedgerBuilder:

    def build(
        self,
        context,
        result,
    ):

        docs = []

        for row in result.rows:

            docs.append({

                "doctype":
                    "Cost Ledger",

                "cost_ledger_cost_entry":
                    context.cost_entry.name,

                "cost_ledger_vin":
                    row["vehicle"],

                "cost_ledger_currency":
                    row["currency"],

                "cost_ledger_exchange_rate":
                    context.exchange_rate,

                "cost_ledger_foreign_amount":
                    row["foreign_amount"],

                "cost_ledger_base_currency":
                    row["base_currency"],

                "cost_ledger_base_amount":
                    row["base_amount"],

                "cost_ledger_remark":
                    row["remark"],

            })

        return docs