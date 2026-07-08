window.vehicle_import = window.vehicle_import || {};

window.vehicle_import.load_vehicle_holder_cost_report = function (frm) {

    const field = frm.get_field(
        "vehicle_holder_cost_report"
    );

    if (!field) {
        return;
    }

    field.$wrapper.empty();

    const wrapper = $(
        `<div style="height:600px;"></div>`
    );

    field.$wrapper.append(
        wrapper
    );

    frappe.call({

        method:
            "vehicle_import.vehicle_import.services.vehicle_holder_cost_report.get_vehicle_holder_cost_report",

        freeze: false,

        args: {

            vehicle_holder:
                frm.doc.name,

        },

        callback(r) {
                    
            if (!r.message) {
                return;
            }

            const datatable = new frappe.DataTable(
                wrapper[0],
                {
                    columns: r.message.columns,
                    data: r.message.rows,
                    inlineFilters: true,
                    checkboxColumn: false,
                    serialNoColumn: false,
                    // dropdownButton: false,
                    layout: "fluid",
                    noDataMessage: __("No costs found."),
                }
            );

            datatable.wrapper.find(".dt-dropdown-container").remove();

            const dir = frappe.utils.is_rtl() ? "rtl" : "ltr";
            datatable.datatableWrapper.dir = dir;

            datatable.datamanager.data.forEach(row => {
                row.vehicle = `<a href="/app/vehicle-unit/${row.vehicle}">${row.vehicle}</a>`;
                row.holder = `<a href="/app/vehicle-holder/${row.holder}">${row.holder}</a>`;
                row.holder_detail = `<a href="/app/vehicle-holder-detail/${row.holder_detail}">${row.holder_detail}</a>`;
                row.reference = `<a href="/app/vehicle-holder/${row.reference}">${row.reference}</a>`;
            });

            datatable.refresh();

        },

    });

};
