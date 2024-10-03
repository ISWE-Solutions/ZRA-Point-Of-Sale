/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { rpc } from "web.rpc";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    async toggleIsToInvoice() {
        // First, call the original toggleIsToInvoice method
        super.toggleIsToInvoice(...arguments);

        // Proceed if the order is marked for invoicing
        if (this.currentOrder.is_to_invoice()) {
            try {
                // Step 1: Prepare the payload from the order
                const orderPayload = this._prepareOrderPayload();

                // Step 2: Send the payload to the external API
                const apiSalesResponse = await this._postToApi("http://localhost:8085/trnsSales/saveSales", orderPayload.sales_payload);
                const apiStockResponse = await this._postToApi("http://localhost:8085/trnsStock/saveStock", orderPayload.stock_payload);

                // Step 3: Save the invoice and the API response
                if (apiSalesResponse && apiSalesResponse.success && apiStockResponse && apiStockResponse.success) {
                    await this._saveInvoiceWithAPIResponse(orderPayload);

                    // Step 4: Print the saved invoice
                    this.set_to_print();
                } else {
                    this.showPopup('ErrorPopup', {
                        title: _t('API Error'),
                        body: _t('Failed to get valid responses from the API.'),
                    });
                }
            } catch (error) {
                this.showPopup('ErrorPopup', {
                    title: _t('Error'),
                    body: _t(`An error occurred: ${error.message}`),
                });
            }
        }
    },

    // Prepare the payload from the current order
    _prepareOrderPayload() {
        const order = this.currentOrder;
        const sales_payload = {
            order_id: order.name,
            amount_total: order.get_total_with_tax(),
            partner_id: order.get_partner() ? order.get_partner().id : null,
            lines: order.get_orderlines().map(line => ({
                product_id: line.product.id,
                quantity: line.get_quantity(),
                price_unit: line.get_price_with_tax(),
            })),
        };
        const stock_payload = {
            order_id: order.name,
            location_id: this.pos.config.stock_location_id,  // Assuming stock_location_id is available in the POS config
            lines: order.get_orderlines().map(line => ({
                product_id: line.product.id,
                quantity: line.get_quantity(),
            })),
        };
        return { sales_payload, stock_payload };
    },

    // Send the payload to the API
    async _postToApi(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });
        return response.json();  // Assuming the API returns a JSON response
    },

    // Save the invoice in Odoo's accounting model
    async _saveInvoiceWithAPIResponse(orderPayload) {
        const invoiceData = {
            move_type: 'out_invoice',
            partner_id: orderPayload.sales_payload.partner_id,
            invoice_line_ids: orderPayload.sales_payload.lines.map(line => [
                0, 0, {
                    product_id: line.product_id,
                    quantity: line.quantity,
                    price_unit: line.price_unit,
                }
            ]),
        };

        // RPC call to create the invoice in account.move
        const result = await rpc({
            model: 'account.move',
            method: 'create',
            args: [invoiceData],
        });

        // Posting the invoice (optional, based on your workflow)
        await rpc({
            model: 'account.move',
            method: 'action_post',
            args: [[result]],  // Posting the created invoice
        });

        return result;
    },
});
