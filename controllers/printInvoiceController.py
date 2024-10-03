from odoo import http
from odoo.http import request
import logging

logger = logging.getLogger(__name__)


class PrintInvoiceController(http.Controller):

    @http.route('/your/custom/print/route', type='json', auth="user", methods=['POST'])
    def print_custom_invoice(self):
        print("Received request to print custom invoice")

        params = request.params.get('params')
        print(f"Here are the params that were received: {params}")

        sequence_number = params.get('sequence_number')

        if sequence_number:
            print(f"Received sequence number: {sequence_number}")

            # Retrieve the invoice using the sequence number
            invoice = request.env['account.move'].search([('sequence_number', '=', sequence_number)], limit=1)
            print(f"Here is the invoice that was found: {invoice}")

            if invoice:
                print(f"Printing invoice with sequence number: {sequence_number}")
                try:
                    # Call the custom print function, returning the PDF URL
                    result = invoice.action_print_custom_invoice_url()
                    return {'success': True, 'report_url': result['report_url']}
                except Exception as e:
                    print(f"Error printing invoice: {e}")
                    return {'success': False, 'message': f'Error printing invoice: {e}'}
            else:
                print(f"Invoice with sequence number {sequence_number} not found")
                return {'success': False, 'message': 'Invoice not found'}
        else:
            print("No sequence number provided")
            return {'success': False, 'message': 'No sequence number provided'}
