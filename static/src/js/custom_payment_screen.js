/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { jsonrpc } from "@web/core/network/rpc_service";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

// Store the original validateOrder method
const originalValidateOrder = PaymentScreen.prototype.validateOrder;

// Create a counter to track orders being processed
let orderCount = 0;

// Patching the PaymentScreen to override validateOrder
patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        console.log("Validate button clicked!");  // Log message when validate button is clicked

        this.numberBuffer.capture();

        // Handle cash rounding if configured
        if (this.pos.config.cash_rounding) {
            if (!this.pos.get_order().check_paymentlines_rounding()) {
                console.log("Rounding error in payment lines");
                this.popup.add(ErrorPopup, {
                    title: _t('Rounding error in payment lines'),
                    body: _t('The amount of your payment lines must be rounded to validate the transaction.'),
                });
                return;
            }
        }

        // Ensure the order is valid
        if (await this._isOrderValid(isForceValidate)) {
            // Remove pending payments before finalizing the validation
            for (const line of this.paymentLines) {
                if (!line.is_done()) {
                    this.currentOrder.remove_paymentline(line);
                }
            }

            // Finalize the order and wait until it's sent to the backend
            await this._finalizeValidation();

            const order = this.pos.get_order();
            const orderId = order.backendId || order.server_id;
            console.log("Order is being processed with ID: ", orderId);

            if (orderId) {
                // Increment the order counter
                orderCount += 1;
                console.log("Number of orders processed: ", orderCount);

                try {
                    // Use jsonrpc to call the backend route for invoice creation
                    const response = await jsonrpc('/your/custom/route', {
                        params: { order_id: orderId },  // Pass the orderId to the backend
                    });

                    // Log the response from the backend
                    console.log("Received response from backend: ", response);

                    // Check if invoice was created successfully and if sequence_number is available
                    if (response.success && response.sequence_number) {
                        console.log("Invoice created successfully with sequence number: ", response.sequence_number);

                        // Check if smart_invoice is enabled for printing
                        if (this.smartInvoiceEnabled) {
                            try {
                                const printResponse = await jsonrpc('/your/custom/print/route', {
                                    params: { sequence_number: response.sequence_number },  // Make sure this is correctly passed
                                });

                                if (printResponse.success && printResponse.report_url) {
                                    console.log("Invoice is being printed");

                                    // Open the PDF report in a new browser tab or window
                                    window.open(printResponse.report_url, '_blank');
                                } else {
                                    console.error("Failed to print the invoice: ", printResponse.message);
                                }

                            } catch (error) {
                                console.error('Error during invoice printing:', error);
                            }
                        } else {
                            console.log('Smart Invoice is not enabled. Skipping invoice printing.');
                        }

                    } else {
                        throw new Error(response.message || 'No sequence number provided');
                    }

                } catch (error) {
                    // Handle any errors during the invoice creation process
                    console.error('Failed to create invoice:', error);
                    this.popup.add(ErrorPopup, {
                        title: _t('Invoice Error'),
                        body: _t(`There was an error creating the invoice: ${error.message}`),
                    });
                }
            } else {
                // Handle case where the order ID could not be retrieved
                console.error('Order ID not found for invoice creation.');
                this.popup.add(ErrorPopup, {
                    title: _t('Order Error'),
                    body: _t('Unable to find order for invoice creation.'),
                });
            }
        }
    }


});
