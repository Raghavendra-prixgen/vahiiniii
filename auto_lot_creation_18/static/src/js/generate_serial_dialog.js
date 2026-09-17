/** @odoo-module */
import { GenerateDialog, GenerateSerials, ImportLots } from "@stock/widgets/generate_serial";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Component, useRef, onMounted } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

patch(GenerateDialog.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.nextSerial = useRef("nextSerial");
        this.nextSerialCount = useRef("nextSerialCount");
        this.totalReceived = useRef("totalReceived");

        onMounted(async () => {
            if (this.props.mode === 'generate') {
                try {
                    // Set default count based on product quantity
                    if (this.nextSerialCount.el) {
                        this.nextSerialCount.el.value = this.props.move.data.product_uom_qty || 1;
                    }
                    
                    // Set total received for lot tracking
                    if (this.props.move.data.has_tracking === 'lot' && this.totalReceived.el) {
                        this.totalReceived.el.value = this.props.move.data.quantity || 1;
                    }

                    // Only fetch sequence if we don't already have a lot name
                    const existingLotName = this.props.move.data.move_line_ids?.records?.[0]?._textvalues?.['lot_name'];
                    if (!existingLotName && this.nextSerial.el) {
                        await this.generateNextSequence();
                    }
                } catch (error) {
                    console.error("Failed to fetch sequence number:", error);
                    this.notification.notify({
                        title: _t("Error"),
                        message: _t("Failed to generate sequence number"),
                        type: 'danger'
                    });
                }
            }
        });
    },

    async generateNextSequence() {
        try {
            const sequence = await this.orm.call(
                "stock.move",
                "get_next_sequence_number",
                [],
                {
                    product_id: this.props.move.data.product_id[0],
                    picking_id: this.props.move.data.picking_id?.[0]
                }
            );
            
            if (sequence && this.nextSerial.el) {
                this.nextSerial.el.value = sequence;
                return true;
            }
            return false;
        } catch (error) {
            console.error("Error generating sequence:", error);
            this.notification.notify({
                title: _t("Error"),
                message: _t("Failed to generate sequence number"),
                type: 'danger'
            });
            return false;
        }
    },

    async generate() {
        if (this.props.mode === 'generate') {
            if (!this.nextSerial.el.value) {
                const success = await this.generateNextSequence();
                if (!success) {
                    return;
                }
            }
        }
        return super.generate();
    },
});