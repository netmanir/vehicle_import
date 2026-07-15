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