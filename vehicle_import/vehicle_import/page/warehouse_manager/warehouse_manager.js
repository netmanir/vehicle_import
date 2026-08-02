frappe.pages["warehouse-manager"].on_page_load = function (wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Warehouse Manager"),
        single_column: true,
    });    
    const manager = new WarehouseManager(page);
    manager.init();
};


class WarehouseManager {

    constructor(page) {
        this.page = page;

        // UI
        this.table = null;

        // Data
        this.warehouses = [];
        this.rules = [];
        this.cost_categories = [];

        // State
        this.selected_warehouse = null;

        this.render();
    }


    async init() {
        await this.load_warehouses();
    }


    render() {
        this.page.main.html(`
            <div class="warehouse-manager mx-5 my-3">
                <div class="warehouse-list mb-4">
                    <div id="warehouse-table"></div>
                </div>
                <hr>
                <div
                    id="warehouse-settings"
                    style="display:none;">
                    <div class="frappe-card p-3 mb-4">
                        <div class="d-flex align-items-center flex-wrap" style="gap:20px;">
                            <div class="d-flex align-items-center" style="gap:8px;">
                                <label class="control-label mb-0">
                                    ${__("Display Order")}
                                </label>
                                <input
                                    id="display-order"
                                    class="form-control"
                                    type="number"
                                    style="width:90px;">
                            </div>
                            <div class="checkbox mb-0">
                                <label class="mb-0">
                                    <input
                                        id="valid-vin-in"
                                        type="checkbox">
                                    ${__("Valid VIN Required for Input")}
                                </label>
                            </div>
                            <div class="checkbox mb-0">
                                <label class="mb-0">
                                    <input
                                        id="valid-vin-out"
                                        type="checkbox">
                                    ${__("Valid VIN Required for Output")}
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="frappe-card p-3 h-100">
                                <h5 class="mb-3">
                                    ${__("Required Cost Categories for Input")}
                                </h5>
                                <div id="input-costs"></div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="frappe-card p-3 h-100">
                                <h5 class="mb-3">
                                    ${__("Required Cost Categories for Output")}
                                </h5>
                                <div id="output-costs"></div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4 text-right">
                        <button
                            id="btn-save"
                            class="btn btn-primary">
                            ${__("Save")}
                        </button>
                    </div>
                </div>
            </div>
        `);

        this.$table =
            this.page.main.find("#warehouse-table");

        this.$settings =
            this.page.main.find("#warehouse-settings");

        this.$input_costs =
            this.page.main.find("#input-costs");

        this.$output_costs =
            this.page.main.find("#output-costs");

        this.create_table();

        this.bind_events();
        this.bind_dirty_events();
    }


    create_table() {
        this.table = new DataTable(this.$table[0], {
            columns: [
                {
                    id: "idx",
                    name: "#",
                },
                {
                    id: "warehouse",
                    name: __("Warehouse"),
                },
                {
                    id: "display_order",
                    name: __("Display Order"),
                },
                {
                    id: "vin_in",
                    name: __("VIN In"),
                    format: value => value ? "✔" : "",
                },
                {
                    id: "vin_out",
                    name: __("VIN Out"),
                    format: value => value ? "✔" : "",
                },
                {
                    id: "input_costs",
                    name: __("Input Costs"),
                    format: cost_category_badges,
                },
                {
                    id: "output_costs",
                    name: __("Output Costs"),
                    format: cost_category_badges,
                },
            ],
            data: [],
            layout: "fluid",
            serialNoColumn: false,
        });
		//
		// RTL
		//
		const dir = frappe.utils.is_rtl() ? "rtl" : "ltr";
		this.table.datatableWrapper.dir = dir;
        // Righ-Align in RTL mode
        const originalRenderRows =
            this.table.bodyRenderer.renderRows.bind(
                this.table.bodyRenderer
            );

        this.table.bodyRenderer.renderRows = (...args) => {
            const result = originalRenderRows(...args);
            if (frappe.utils.is_rtl()) {
                this.table.datatableWrapper
                    .querySelectorAll(
                        ".dt-cell > .dt-cell__content:not(.dt-cell__content--col-0)"
                    )
                    .forEach(el => {
                        el.style.textAlign = "right";
                    });
            }
            
            return result;
        };

        
		//
		// Height
		//
		this.table.bodyScrollable.style.maxHeight = "35vh";
		this.table.bodyScrollable.style.overflowY = "auto";
    }


    bind_events() {

        //
        // Warehouse Row Click
        //
        this.$table.on("click", ".dt-row", async (e) => {
            const row_index = Number(
                $(e.currentTarget).attr("data-row-index")
            );
            const warehouse = this.warehouses[row_index];
            if (!warehouse) {
                return;
            }
            if (
                this.is_dirty &&
                this.current_warehouse &&
                this.current_warehouse !== warehouse.name
            ) {
                frappe.confirm(
                    __("Current changes are not saved. Save them?"),
                    async () => {
                        await this.save_warehouse_settings();
                        this.highlight_selected_row(row_index);
                        this.current_warehouse = warehouse.name;
                        await this.load_warehouse_settings(warehouse.name);
                    },
                    async () => {
                        this.is_dirty = false;
                        this.highlight_selected_row(row_index);
                        this.current_warehouse = warehouse.name;
                        await this.load_warehouse_settings(warehouse.name);
                    }
                );
                return;
            }
            this.highlight_selected_row(row_index);
            this.current_warehouse = warehouse.name;
            await this.load_warehouse_settings(warehouse.name);
        });


        //
        // Save Button
        //
        this.page.main.find("#btn-save").on("click", async () => {
            await this.save_warehouse_settings();
        });
    }


    async load_warehouses() {
        const { message } = await frappe.call({
            method:
                "vehicle_import.vehicle_import.services.warehouse_manager.get_warehouses"

        });
        this.warehouses = message || [];
        this.table.refresh(
            this.get_table_data()
        );
    }


    async load_warehouse_settings(warehouse) {
        this.selected_warehouse = warehouse;
        const { message } = await frappe.call({
            method:
                "vehicle_import.vehicle_import.services.warehouse_manager.get_warehouse_settings",

            args: {
                warehouse: warehouse
            }
        });
        this.rules = message.rules || [];
        this.cost_categories =
            message.cost_categories || [];

        //
        // Show editor
        //
        this.$settings.show();

        //
        // Order
        //
        this.page.main
            .find("#display-order")
            .val(
                this.get_rule_value(
                    "Display Order"
                ) || ""
            );


        //
        // Valid VIN
        //
        this.page.main
            .find("#valid-vin-in")
            .prop(
                "checked",
                !!this.get_rule(
                    "Valid VIN",
                    "In"
                )
            );

        this.page.main
            .find("#valid-vin-out")
            .prop(
                "checked",
                !!this.get_rule(
                    "Valid VIN",
                    "Out"
                )
            );


        //
        // Cost Categories
        //
        this.render_input_costs();
        this.render_output_costs();

        this.is_dirty = false;
    }


    render_input_costs() {
        let html = "";
        this.cost_categories.forEach(category => {
            const checked = !!this.get_rule(
                "Cost Category",
                "In",
                category.name
            );
            html += `
                <div class="checkbox">
                    <label>
                        <input
                            type="checkbox"
                            class="wm-input-cost"
                            value="${category.name}"
                            ${checked ? "checked" : ""}>
                        ${category.cost_category_title}
                    </label>
                </div>
            `;
        });
        this.$input_costs.html(html);
    }


    render_output_costs() {
        let html = "";
        this.cost_categories.forEach(category => {
            const checked = !!this.get_rule(
                "Cost Category",
                "Out",
                category.name
            );
            html += `
                <div class="checkbox">
                    <label>
                        <input
                            type="checkbox"
                            class="wm-output-cost"
                            value="${category.name}"
                            ${checked ? "checked" : ""}>
                        ${category.cost_category_title}
                    </label>
                </div>
            `;
        });
        this.$output_costs.html(html);
    }


    get_rule(rule_type, direction = null, value = null) {
        return this.rules.find(r =>
            r.rule_type === rule_type &&
            (direction == null || r.direction === direction) &&
            (value == null || r.rule_value === value)
        );
    }


    get_rule_value(rule_type) {
        return this.get_rule(rule_type)?.rule_value;
    }


    highlight_selected_row(row_index) {
        if (this.selected_row_index != null) {
            this.table.rowmanager.highlightRow(
                this.selected_row_index,
                false
            );
        }

        this.table.rowmanager.highlightRow(
            row_index,
            true
        );

        this.selected_row_index = row_index;
    }


    bind_dirty_events() {
        this.$settings.on(
            "change input",
            "input, select, textarea",
            () => {
                this.is_dirty = true;
            }
        );
    }

    
    async save_warehouse_settings() {
        if (!this.current_warehouse) {
            return;
        }
        const input_cost_categories = [];
        this.$input_costs
            .find("input[type='checkbox']:checked")
            .each(function () {
                input_cost_categories.push(this.value);
            });
        const output_cost_categories = [];
        this.$output_costs
            .find("input[type='checkbox']:checked")
            .each(function () {
                output_cost_categories.push(this.value);
            });
        await frappe.call({
            method:
                "vehicle_import.vehicle_import.services.warehouse_manager.save_warehouse_settings",
            args: {
                warehouse: this.current_warehouse,
                display_order: cint($("#display-order").val()) || 0,
                valid_vin_required_for_input: $("#valid-vin-in").prop("checked"),
                valid_vin_required_for_output: $("#valid-vin-out").prop("checked"),
                input_cost_categories,
                output_cost_categories
            }
        });

        this.is_dirty = false;

        // Update Display Order in DatatTable
        const row_index = this.warehouses.findIndex(
            w => w.name === this.current_warehouse
        );

        if (row_index >= 0) {
            const warehouse =
                this.warehouses[row_index];

            warehouse.display_order =
                cint($("#display-order").val()) || 0;

            warehouse.valid_vin_required_for_input =
                $("#valid-vin-in").prop("checked");

            warehouse.valid_vin_required_for_output =
                $("#valid-vin-out").prop("checked");

            warehouse.input_cost_categories =
                [...input_cost_categories];

            warehouse.output_cost_categories =
                [...output_cost_categories];

            this.table.refresh(
                this.get_table_data()
            );
            this.highlight_selected_row(row_index);
        }

        frappe.show_alert({
            message: __("Warehouse settings saved."),
            indicator: "green"
        });
    }

    get_table_data() {
        return this.warehouses.map((w, i) => [
            i + 1,
            w.name,
            w.display_order ?? "",
            w.valid_vin_required_for_input,
            w.valid_vin_required_for_output,
            w.input_cost_categories,
            w.output_cost_categories,
        ]);
    }
}

function cost_category_badges(
    value,
    cells,
    column,
    row
) {
    const values = row[column.colIndex];

    if (!values?.length) {
        return "";
    }

    return `
        <div class="wm-cost-badges">
            ${values.map(category => `
                <span class="badge badge-secondary p-2">
                    ${__(category)}
                </span>
            `).join("")}
        </div>
    `;
}
