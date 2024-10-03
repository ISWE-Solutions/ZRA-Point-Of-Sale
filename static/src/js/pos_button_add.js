/**@odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
patch(PaymentScreen.prototype, {

smart_invoice() {
    // Toggle the state of Smart Invoice
    if (this.smartInvoiceEnabled === undefined) {
        this.smartInvoiceEnabled = false;  // Initialize state if not already set
    }

    this.smartInvoiceEnabled = !this.smartInvoiceEnabled;  // Toggle the state
    console.log("Smart Invoice state:", this.smartInvoiceEnabled);

    // Optional: Trigger a re-render or update the UI if needed
    this.render(); // This method might be necessary depending on how your component updates
}



})