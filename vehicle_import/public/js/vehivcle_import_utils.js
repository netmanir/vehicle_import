window.vehicle_import = window.vehicle_import || {};

window.vehicle_import.show_loading = function (wrapper, message) {
    wrapper.html(`
        <div class="text-center text-muted p-5">
            <div class="spinner-border" role="status"></div>
            <div class="mt-2">
                ${message || __("Loading data...")}
            </div>
        </div>
    `);
};


window.vehicle_import.bind_tab_refresh = function (
    frm, 
    tab_fieldname, 
    namespace, 
    callback,
    delay = 50
) {
    const tab = frm.layout.tabs.find(
        t => t.df.fieldname === tab_fieldname
    );
    if (!tab || !tab.tab_link) {
        return;
    }
    callback();
    tab.tab_link
        .off(`click.${namespace}`)
        .on(`click.${namespace}`, () => {
            setTimeout(callback, delay);
        });
}

window.vehicle_import.bind_datatable_row_click = function (
    datatable,
    callback
) {
    $(datatable.datatableWrapper)
        .off("click.vehicle_import_row")
        .on(
            "click.vehicle_import_row",
            ".dt-row",
            function () {
                const row = datatable.datamanager.data[
                    Number(this.dataset.rowIndex)
                ];
                callback(row);
            }
        );
};