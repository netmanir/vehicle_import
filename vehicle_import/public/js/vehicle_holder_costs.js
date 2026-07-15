window.vehicle_import = window.vehicle_import || {};

window.vehicle_import.load_vehicle_holder_costs = function (frm) {

    const field = frm.get_field(
        "vehicle_holder_costs"
    );

    if (!field) {
        return;
    }

    field.$wrapper.empty();

    const summary = $(`
        <div class="vehicle-holder-costs-summary"></div>
    `);

    const wrapper = $(
        `<div></div>`
    );

    field.$wrapper.append(summary);
    field.$wrapper.append(wrapper);

    vehicle_import.show_loading(
        wrapper,
        __("Loading data...")
    );

    frappe.call({
        method:
            "vehicle_import.vehicle_import.services.vehicle_holder_costs.get_vehicle_holder_costs",
        freeze: false,
        args: {
            vehicle_holder: frm.doc.name,
        },

        callback(r) {

            if (!r.message) {
                return;
            }

            wrapper.empty();

            //
            // Format Columns
            //
            // r.message.columns.forEach(col => {

            //     switch (col.id) {

            //         case "vin":
            //             col.format = (value, row, column, data) =>
            //                 `<a target="_blank" href="/app/vehicle-unit/${data.vehicle}">${value}</a>`;
            //             break;

            //         case "cost_holder":
            //             col.format = value =>
            //                 `<a target="_blank" href="/app/vehicle-holder/${value}">${value}</a>`;
            //             break;
            //     }

            // });

            //
            // DataTable
            //
            const datatable = new frappe.DataTable(
                wrapper[0],
                {
                    columns: r.message.columns,
                    data: r.message.rows,
                    inlineFilters: true,
                    checkboxColumn: false,
                    serialNoColumn: true,
                    layout: "fluid",
                    noDataMessage: __("No costs found."),
                }
            );

            const dir = frappe.utils.is_rtl() ? "rtl" : "ltr";
            datatable.datatableWrapper.dir = dir;

            const originalRenderRows =
                datatable.bodyRenderer.renderRows.bind(
                    datatable.bodyRenderer
                );
            datatable.bodyRenderer.renderRows = function (...args) {
                const result = originalRenderRows(...args);
                refresh_costs_summary(
                    summary,
                    datatable,
                    frm.doc.name,
                );

                // Righ-Align in RTL mode
                if (frappe.utils.is_rtl()) {
                    datatable.datatableWrapper
                        .querySelectorAll(".dt-cell:not(.dt-cell--header) > .dt-cell__content:not(.dt-cell__content--col-0)")
                        .forEach(el => {
                            el.style.textAlign = "right";
                        });
                }

                return result;
            };

            datatable.refresh();         
        },
    });
};

function refresh_costs_summary(
    summary,
    datatable,
    vehicle_holder,
) {
    const dm = datatable.datamanager;
    const rows = dm
        .getFilteredRowIndices()
        .map(i => dm.data[i]);

    const total = rows.reduce(
        (sum, row) => sum + flt(row.base_amount_raw || 0),
        0
    );

    if (!summary.data("initialized")) {
        summary.html(`
            <span>
                ${__("Records")}:
                <b class="summary-records"></b>
            </span>
            <span>
                ${__("Total Amount")}:
                <b class="summary-amount"></b>
            </span>
            <button class="btn btn-primary btn-sm export-costs">
                ${__("Export to Excel")}
            </button>
        `);

        summary.find(".export-costs").on("click", () => {
            window.open(
                `/api/method/vehicle_import.vehicle_import.services.vehicle_holder_costs.export_vehicle_holder_costs?vehicle_holder=${vehicle_holder}`
            );
        });
        summary.data("initialized", true);
    }
    summary.find(".summary-records").text(
        rows.length
    );
    summary.find(".summary-amount").text(
        format_number(total, null, 0)
    );

    // Add fade effect
    const records = summary.find(".summary-records");
    const amount = summary.find(".summary-amount");
    records.text(rows.length);
    amount.text(format_number(total, null, 0));
    records.addClass("summary-updated");
    amount.addClass("summary-updated");
    setTimeout(() => {
        records.removeClass("summary-updated");
        amount.removeClass("summary-updated");
    }, 500);
}