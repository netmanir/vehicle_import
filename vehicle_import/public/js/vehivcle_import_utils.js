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

window.vehicle_import.format_compact_amount = function (amount) {

    amount = Number(amount || 0);

    if (amount >= 1_000_000_000) {
        return (amount / 1_000_000_000).toLocaleString(undefined, {maximumFractionDigits: 2,}) + ` ${__("B")}`;
    }

    if (amount >= 1000000) {
        return (amount / 1_000_000).toFixed(1).toLocaleString() + ` ${__("M")}`;
    }

    if (amount >= 1_000) {
        return (amount / 1_000).toFixed(1).toLocaleString() + ` ${__("K")}`;
    }

    return amount.toLocaleString();
};



// --------------------------
// DataTable Filters
// --------------------------

window.vehicle_import.datatable_filters = {};

//
// Resolve actual column id
//
const normalize = s =>
    String(s)
        .trim()
        .replace(/\u00A0/g, " ")
        .replace(/\u200C/g, "")
        .replace(/ي/g, "ی")
        .replace(/ك/g, "ک");

window.vehicle_import.datatable_filters.attach = function ({
    datatable,
    filters,
}) {

    if (!datatable || !filters?.length) {
        return;
    }

    //
    // Build Column Map
    //
    const column_map = {};
    datatable.datamanager.columns.forEach(col => {
        column_map[
            normalize(col.id)
        ] = col.id;
    });

    //
    // Internal State
    //
    datatable.__vehicle_import =
        datatable.__vehicle_import || {
            filters: {},
            values: {},
            dropdown: null,
            cache_built: false,
        };

    datatable.__vehicle_import.column_map =
        column_map;

    //
    // Patch renderHeader once
    //
    if (!datatable.__vehicle_import.header_patched) {
        const originalRenderHeader =
            datatable.renderHeader.bind(datatable);

        datatable.renderHeader = function () {
            originalRenderHeader();

            vehicle_import.datatable_filters.attach({
                datatable,
                filters,
            });
        };

        datatable.__vehicle_import.header_patched = true;
    }

    if (!datatable.__vehicle_import.original_data) {
        datatable.__vehicle_import.original_data = [
            ...datatable.options.data
        ];
    }

    //
    // Build cache (only once)
    //
    if (!datatable.__vehicle_import.cache_built) {

        filters.forEach(column_name => {

            const real_column =
                column_map[
                    normalize(column_name)
                ];

            if (!real_column) {
                return;
            }

            const values = new Set();

            datatable.__vehicle_import.original_data.forEach(row => {

                const value =
                    row[real_column];

                if (
                    value !== undefined &&
                    value !== null &&
                    value !== ""
                ) {
                    values.add(value);
                }
            });

            datatable.__vehicle_import.values[
                real_column
            ] = [...values].sort((a, b) =>
                String(a).localeCompare(
                    String(b),
                    frappe.boot.lang || "en"
                )
            );

            datatable.__vehicle_import.filters[
                real_column
            ] = [
                ...datatable.__vehicle_import.values[
                    real_column
                ]
            ];
        });

        datatable.__vehicle_import.cache_built = true;
    }

    //
    // Replace Header Inputs
    //
    filters.forEach(column_name => {

        const real_column =
            column_map[
                normalize(column_name)
            ];

        if (!real_column) {
            return;
        }

        const column =
            datatable.datamanager.columns.find(
                c => c.id === real_column
            );

        if (!column) {
            return;
        }

        const input =
            datatable.datatableWrapper.querySelector(
                `.dt-filter[data-col-index="${column.colIndex}"]`
            );

        if (!input) {
            return;
        }

        input.readOnly = true;
        input.style.cursor = "pointer";
        input.placeholder = "▼";

        if (!input.__vehicle_import_bound) {

            input.addEventListener("click", () => {

                vehicle_import.datatable_filters.show(
                    datatable,
                    real_column,
                    input
                );
            });

            input.__vehicle_import_bound = true;
        }
    });
};

window.vehicle_import.datatable_filters.get_filtered_rows =
    function (datatable) {
        const dm = datatable.datamanager;
        return dm
            .getFilteredRowIndices()
            .map(i => dm.data[i]);
    };

window.vehicle_import.datatable_filters.show = function (
    datatable,
    column_name,
    input
) {
    const actual_column =
        datatable.__vehicle_import.column_map[
            normalize(column_name)
        ];

    if (!actual_column) {
        return;
    }

    //
    // Create once
    //
    if (!datatable.__vehicle_import.dropdown) {
        const dropdown =
            document.createElement("div");

        dropdown.className =
            "vehicle-import-filter-dropdown";

        dropdown.style.display = "none";

        datatable.datatableWrapper.appendChild(
            dropdown
        );

        datatable.__vehicle_import.dropdown =
            dropdown;
    }

    const dropdown =
        datatable.__vehicle_import.dropdown;

    //
    // Bind Events
    //
    if (!dropdown.__events_bound) {

        dropdown.addEventListener(
            "click",
            function (e) {

                //
                // Apply
                //
                if (e.target.matches(".apply")) {

                    const column =
                        dropdown.__column;

                    const selected = [
                        ...dropdown.querySelectorAll(
                            "input[type=checkbox]:checked"
                        )
                    ].map(c => c.value);

                    datatable.__vehicle_import.filters[
                        column
                    ] = selected;

                    vehicle_import.datatable_filters.apply(
                        datatable
                    );

                    dropdown.style.display = "none";
                }

                //
                // Reset
                //
                if (e.target.matches(".reset")) {

                    const column =
                        dropdown.__column;

                    //
                    // Restore all possible values
                    //
                    datatable.__vehicle_import.filters[
                        column
                    ] = [
                        ...datatable.__vehicle_import.values[
                            column
                        ]
                    ];

                    vehicle_import.datatable_filters.apply(
                        datatable
                    );

                    dropdown.style.display = "none";
                }
            }
        );

        dropdown.__events_bound = true;
    }

    //
    // Toggle
    //
    if (
        dropdown.style.display === "block" &&
        dropdown.__column === actual_column
    ) {
        dropdown.style.display = "none";
        return;
    }

    dropdown.__column =
        actual_column;

    dropdown.replaceChildren();

    (
        datatable.__vehicle_import.values[
            actual_column
        ] || []
    ).forEach(value => {

        const checked =
            datatable.__vehicle_import.filters[
                actual_column
            ].includes(value);

        dropdown.insertAdjacentHTML(
            "beforeend",
            `
            <label class="vehicle-import-filter-item">
                <input
                    type="checkbox"
                    value="${value}"
                    ${checked ? "checked" : ""}
                >
                ${value}
            </label>
            `
        );
    });

    dropdown.insertAdjacentHTML(
        "beforeend",
        `
        <div class="vehicle-import-filter-buttons">
            <button class="btn btn-primary btn-xs apply">
                ${__("Apply")}
            </button>
            <button class="btn btn-default btn-xs reset">
                ${__("Reset")}
            </button>
        </div>
        `
    );

    //
    // Position
    //
    const inputRect =
        input.getBoundingClientRect();

    const wrapperRect =
        datatable.datatableWrapper.getBoundingClientRect();

    dropdown.style.display = "block";

    const dropdownWidth =
        dropdown.offsetWidth;

    let left =
        inputRect.left - wrapperRect.left;

    //
    // Prevent overflow on the right
    //
    left = Math.min(
        left,
        wrapperRect.width - dropdownWidth - 5
    );

    //
    // Prevent overflow on the left
    //
    left = Math.max(
        left,
        5
    );

    dropdown.style.left =
        left + "px";

    dropdown.style.top =
        (inputRect.bottom - wrapperRect.top + 5) + "px";
};

//
// Apply current filters
//
// Never patch Frappe DataTable internals.
// Always keep original dataset and refresh DataTable with filtered rows.
//
window.vehicle_import.datatable_filters.apply = function (datatable) {

    const original =
        datatable.__vehicle_import.original_data;

    const filters =
        datatable.__vehicle_import.filters;

    const column_map =
        datatable.__vehicle_import.column_map;

    const filtered = original.filter(row => {

        for (const column_name in filters) {

            const allowed =
                filters[column_name];

            //
            // Nothing selected -> show nothing
            //
            if (allowed.length === 0) {
                return false;
            }

            const real_column =
                column_map[column_name] || column_name;

            if (
                !allowed.includes(
                    row[real_column]
                )
            ) {
                return false;
            }
        }

        return true;
    });

    datatable.refresh(filtered);
};

