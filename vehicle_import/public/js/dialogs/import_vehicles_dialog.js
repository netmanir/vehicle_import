class ImportVehicles_Dialog {

    static async show(options = {}) {

        const import_vehicle_dialog = new ImportVehicles_Dialog(options);
        return await import_vehicle_dialog.show();
    }

    constructor(options = {}) {

        // Configuration
        this.options = options;

        // UI
        this.dialog = null;
        this.holder_table = null;
        this.detail_table = null;
        this.history_table = null;

        // Data
        this.holders = [];
        this.details = [];
        this.histories = [];
    }


    async show() {

        this.create_dialog();

        return new Promise((resolve) => {

            this.dialog.set_primary_action(__("Import"), () => {
                resolve(this.get_result());
                this.dialog.hide();
            });

            this.dialog.get_close_btn().on("click", () => {
                resolve(null);
            });

            this.dialog.show();        
            
            // Create Table
            this.dialog.$wrapper.one("shown.bs.modal", async () => {
                this.create_tables();
                this.bind_events();
                await this.load_holders();
            });

        });

    }

    create_dialog() {

        this.dialog = new frappe.ui.Dialog({
            title: __("Vehicle Holder Explorer"),
            size: "extra-large",
            fields: [
                {
                    fieldtype: "HTML",
                    fieldname: "explorer_html"
                }
            ]
        });

        this.dialog.$wrapper.find(".modal-dialog").css({
            width: "95vw",
            "max-width": "95vw"
        });
        this.dialog.$wrapper.find(".modal-content").css({
            height: "92vh",
            display: "flex"
        });

        this.dialog.$wrapper.find(".modal-body").css({
            flex: 1,
            overflow: "hidden"
        });

        const html = `
            <div class="vehicle-holder-explorer" style="display:flex; flex-direction:column; height:100%;">

                <div class="mb-3">
                    <label class="control-label">${__("Search Holder")}</label>
                    <input
                        id="vhe-search"
                        class="form-control"
                        type="text"
                        placeholder="${__("Search by Title or Document No")}"
                    >
                </div>

                <div class="vhe-top-row"
                    style="display:flex; gap:12px; flex:1; min-height:220px;">

                    <div class="vhe-section"
                        style="display:flex; flex-direction:column; flex:1; min-width:0;">

                        <label class="control-label">
                            ${__("Vehicle Holders")}
                        </label>

                        <div id="vhe-holder-table"
                            style="flex:1;"></div>

                    </div>

                    <div class="vhe-section"
                        style="display:flex; flex-direction:column; flex:1; min-width:0;">

                        <label class="control-label">
                            ${__("Vehicle Holder Details")}
                        </label>

                        <div id="vhe-detail-table"
                            style="flex:1;"></div>

                    </div>

                </div>

                <div class="vhe-section"
                    style="display:flex; flex-direction:column; flex:2; min-height:0; margin-top:12px;">

                    <label class="control-label">
                        ${__("Vehicles")}
                    </label>

                    <div id="vhe-history-table"
                        style="flex:1;"></div>

                </div>

            </div>
         `;

        this.dialog.fields_dict.explorer_html.$wrapper.html(html);

        this.$search =
            this.dialog.fields_dict.explorer_html.$wrapper.find("#vhe-search");

        this.$holder =
            this.dialog.fields_dict.explorer_html.$wrapper.find("#vhe-holder-table");

        this.$detail =
            this.dialog.fields_dict.explorer_html.$wrapper.find("#vhe-detail-table");

        this.$history =
            this.dialog.fields_dict.explorer_html.$wrapper.find("#vhe-history-table");
    }

    create_tables() {

        this.holder_table = new DataTable(this.$holder[0], {
            columns: [
                { name: __("Type") },
                { name: __("Title") },
                { name: __("Document No") }
            ],
            data: [],
            layout: "fluid",
            serialNoColumn: false
        });

        this.detail_table = new DataTable(this.$detail[0], {
            columns: [
                { name: __("Item") },
                { name: __("Quantity") },
                { name: __("Remark") }
            ],
            data: [],
            layout: "fluid",
            serialNoColumn: false
        });

        this.history_table = new DataTable(this.$history[0], {
            checkboxColumn: true,
            columns: [
                { name: __("Vehicle") },
                { name: __("Remark") },
            ],
            data: [],
            layout: "fluid",
            serialNoColumn: false
        });


        // Set Style
        const dir = frappe.utils.is_rtl() ? "rtl" : "ltr";
        this.holder_table.datatableWrapper.dir = dir;
        this.detail_table.datatableWrapper.dir = dir;
        this.history_table.datatableWrapper.dir = dir;
        this.holder_table.bodyScrollable.style.maxHeight = "22vh";
        this.holder_table.bodyScrollable.style.overflowY = "auto";
        this.detail_table.bodyScrollable.style.maxHeight = "22vh";
        this.detail_table.bodyScrollable.style.overflowY = "auto";
        this.history_table.bodyScrollable.style.maxHeight = "35vh";
        this.history_table.bodyScrollable.style.overflowY = "auto";
        this.history_table.style.setStyle(".dt-cell--col-0", {
            width: "50px"
        });
        this.history_table.style.setStyle(".dt-cell__content--col-0", {
            width: "50px"
        });
        this.history_table.style.setStyle(".dt-cell--header-0", {
            width: "50px"
        });
        this.history_table.style.setStyle(".dt-cell__content--header-0", {
            width: "50px"
        });
        const cls = this.history_table.style.scopeClass;
        this.history_table.style.styleEl.sheet.insertRule(`
            .${cls} .dt-cell__content--header-0{
                width:50px !important;
                min-width: 50px !important;
                max-width: 50px !important;
                padding: 8px !important;
            }
        `);

        this.history_table.style.styleEl.sheet.insertRule(`
            .${cls} .dt-cell__content--col-0{
                width: auto !important;
            }
        `);
    }

    bind_events() {

        let search_timeout = null;

        // Holder Search
        this.$search.on("input", () => {
            clearTimeout(search_timeout);

            search_timeout = setTimeout(() => {
                this.load_holders(this.$search.val().trim());
            }, 500);
        });


        // Holder Row Click
        this.$holder.on("click", ".dt-row", (e) => {

            const rowIndex = Number($(e.currentTarget).attr("data-row-index"));

            this.selected_holder = this.holders[rowIndex];
            this.selected_detail = null;

            this.detail_table.refresh([]);
            this.reset_history_table();

            this.load_details(this.selected_holder.name);
        });


        // Detail Row Click
        this.$detail.on("click", ".dt-row", (e) => {

            const rowIndex = Number($(e.currentTarget).attr("data-row-index"));

            this.selected_detail = this.details[rowIndex];

            this.reset_history_table();

            this.load_histories(this.selected_detail.name);
        });

    }

    reset_history_table() {

        this.history_table.rowmanager.checkMap = [];
        this.history_table.refresh([]);

    }

    async load_holders(search = "") {

        const r = await frappe.call({
            method: "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.get_holders",
            args: {
                search: search,
                exclude_holder: this.options.current_holder || null
            }
        });

        this.holders = r.message;

        this.selected_holder = null;
        this.selected_detail = null;

        this.holder_table.refresh(
            this.holders.map(h => [
                h.vehicle_holder_type,
                h.vehicle_holder_title,
                h.vehicle_holder_doc_nr
            ])
        );

        this.detail_table.refresh(
            [],
            this.detail_table.options.columns
        );

        this.history_table.refresh(
            [],
            this.history_table.options.columns
        );
    }

    async load_details(holder_name) {

        const r = await frappe.call({
            method: "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.get_holder_details",
            args: {
                holder_name: holder_name
            }
        });

        this.details = r.message;

        this.selected_detail = null;

        this.detail_table.refresh(
            this.details.map(d => [
                d.vehicle_holder_detail_item,
                d.vehicle_holder_detail_quantity,
                d.vehicle_holder_detail_remark
            ])
        );

        this.history_table.refresh(
            [],
            this.history_table.options.columns
        );
    }

    async load_histories(detail_name) {

        const r = await frappe.call({
            method:
                "vehicle_import.vehicle_import.doctype.vehicle_holder.vehicle_holder.get_holder_histories",
            args: {
                current_holder: this.options.current_holder,
                reference_detail_name: detail_name,
            },
        });

        this.histories = r.message;

        this.history_table.refresh(
            this.histories.map(h => [
                h.vehicle,
                h.vehicle_history_remark
            ])
        );
    }

    get_result() {

        return {
            holder: this.selected_holder,
            detail: this.selected_detail,
            vehicles: this.histories.filter(
                (_, index) => this.history_table.rowmanager.checkMap[index]
            )
        };
    }
}