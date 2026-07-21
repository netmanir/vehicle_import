(() => {

    // فقط برای کاربران فارسی
    if (!frappe?.boot || frappe.boot.lang !== "fa") {
        return;
    }

    console.log("Vehicle Import Jalali Loaded");

    const originalRefreshInput = frappe.ui.form.ControlDate.prototype.refresh_input;
    frappe.ui.form.ControlDate.prototype.refresh_input = function () {
        originalRefreshInput.apply(this, arguments);
        if (this.input) {
            this.input.dispatchEvent(new Event("change", { bubbles: true }));
        }
    };

    // ---------------------------------------------------------
    // Patch JalaliDatePicker
    // ---------------------------------------------------------

    if (!jalaliDatepicker._frappePatched) {

        jalaliDatepicker._frappePatched = true;

        const originalSetTargetValue = jalaliDatepicker.setTargetValue;

        jalaliDatepicker.setTargetValue = function () {

            originalSetTargetValue.apply(this, arguments);

            if (!this.options.targetValueInput) {
                return;
            }

            const targets =
                this.options.targetValueInput instanceof HTMLElement
                    ? [this.options.targetValueInput]
                    : document.querySelectorAll(this.options.targetValueInput);

            for (const input of targets) {

                const control = input._control;

                if (control) {
                    control.validate_and_set_in_model(
                        input.value,
                        null,
                        true
                    );
                }
            }
        };
    }

    // ---------------------------------------------------------
    // Replace Frappe DatePicker
    // ---------------------------------------------------------
    frappe.ui.form.ControlDate.prototype.set_datepicker = function () {

        if (this._jalali_initialized) {
            return;
        }

        this._jalali_initialized = true;

        const hidden = this.input;

        // برای Patch بالا
        hidden._control = this;

        // مخفی کردن Date Input اصلی
        hidden.style.display = "none";

        // ساخت Input نمایشی
        const visible = document.createElement("input");

        visible.type = "text";
        visible.className = hidden.className + " jdp-visible-input";

        visible.tabIndex = hidden.tabIndex;
        visible.readOnly = hidden.readOnly;
        visible.disabled = hidden.disabled;

        hidden.parentNode.appendChild(visible);

        // اتصال DatePicker
        jalaliDatepicker.startWatch({
            autoShow: false,
            targetValueInput: hidden,
            targetValueType: "gregorian"
        });

        visible.addEventListener("focus", () => {
            jalaliDatepicker.show(visible);
        });

        // Sync Gregorian -> Jalali
        const sync = () => {

            visible.readOnly = hidden.readOnly;
            visible.disabled = hidden.disabled;

            if (!hidden.value) {

                if (visible.value) {
                    visible.value = "";
                }

                return;
            }

            const [gy, gm, gd] = hidden.value.split("-").map(Number);

            const j = jalaali.toJalaali(gy, gm, gd);

            const jalaliValue =
                `${j.jy}/${String(j.jm).padStart(2, "0")}/${String(j.jd).padStart(2, "0")}`;

            if (visible.value !== jalaliValue) {
                visible.value = jalaliValue;
            }
        };

        hidden.addEventListener("change", sync);
        hidden.addEventListener("input", sync);

        sync();
        requestAnimationFrame(sync);
    };


    // ---------------------------------------------------------
    // Patch frappe.format to convert to Jalali Date
    // ---------------------------------------------------------
    const originalFormat = frappe.format;
    frappe.format = function (value, df, options, doc) {
        if (
            frappe.boot.lang === "fa" &&
            df &&
            df.fieldtype === "Date" &&
            value
        ) {
            const [gy, gm, gd] = value.split("-").map(Number);
            if (gy) {
                const j = jalaali.toJalaali(gy, gm, gd);

                return `${j.jy}/${String(j.jm).padStart(2, "0")}/${String(j.jd).padStart(2, "0")}`;
            }
        }
        return originalFormat.call(this, value, df, options, doc);
    };

})();