frappe.pages["excel-browser"].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Excel Browser"),
        single_column: true,
    });

    page.set_primary_action(
        __("Refresh"),
        () => load_files(page)
    );


    load_files(page);
};

function load_files(page) {

    page.body.empty();

    vehicle_import.show_loading(
        page.body,
        __("Scanning Excel files...")
    );

    frappe.call({
        method:
            "vehicle_import.vehicle_import.services.excel_browser.get_excel_files",

        callback(r) {
            page.body.empty();
            if (!r.message.length) {
                page.body.html(`
					<div class="text-muted">
						${__("No Excel files found.")}
					</div>
				`);
                return;
            }

            const container = $('<div class="excel-browser-container"></div>');

            page.body.empty();
            page.body.append(container);

            const files_wrapper = $("<div></div>");
            container.append(files_wrapper);

            const excel_wrapper  = $(`<div class="mt-3 pt-3 excel-browser-excel-wrapper"></div>`);
            container.append(excel_wrapper );

            const datatable = new frappe.DataTable(
                files_wrapper[0],
                {
                    columns: [
                        {
                            id: "file",
                            name: __("Report"),
                        },
                        // {
                        // 	id: "size",
                        // 	name: __("Size"),
                        // 	width: 120,
                        // },
                        {
                            id: "modified",
                            name: __("Date Modified"),
                            width: 180,
                        },
                    ],

                    events: {
                        onRowClick(row) {
                            console.log(row);
                        }
                    },

                    data: r.message,

                    checkboxColumn: false,
                    serialNoColumn: false,
                    inlineFilters: false,
                    layout: "fluid",
                }
            );
            datatable.datatableWrapper.dir =
                frappe.utils.is_rtl() ? "rtl" : "ltr";

            vehicle_import.bind_datatable_row_click(
                datatable,
                row => load_excel(excel_wrapper, row.file)
            );
        }
    });

    function load_excel(excel_wrapper, filename) {
        vehicle_import.show_loading(excel_wrapper);
        
        frappe.call({
            method:
                "vehicle_import.vehicle_import.services.excel_browser.get_excel_table",
            args: {
                filename
            },
            callback(r) {
                render_excel_table(excel_wrapper, r.message);
            }
        });
    }

    function render_excel_table(excel_wrapper, data) {
        excel_wrapper.empty();
        const datatable =
            new frappe.DataTable(
                excel_wrapper[0],
                {
                    columns: data.columns,
                    data: data.rows,
                    serialNoColumn: true,
                    inlineFilters: true,
                    checkboxColumn: false,
                    layout: "fluid",
                }
            );
        datatable.datatableWrapper.dir =
            frappe.utils.is_rtl() ? "rtl" : "ltr";
    }
}