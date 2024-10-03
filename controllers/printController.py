from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PosInvoiceController(http.Controller):

    @http.route('/your/custom/invoice_route', type='json', auth="user", methods=['POST'])
    def get_invoice_data(self):
        _logger.info("Received request to retrieve invoice data")

        params = request.params
        sequence_number = params.get('sequence_number')

        if sequence_number:
            # Search for the invoice using the sequence_number
            invoice = request.env['account.move'].search([('sequence_number', '=', sequence_number)], limit=1)
            if invoice:
                _logger.info(f"Invoice with sequence number {sequence_number} found")

                # Prepare the invoice data to be printed (adjust this to fit your specific needs)
                invoice_data = invoice._get_printable_invoice_data()  # Hypothetical method to generate the printable data

                return {'success': True, 'invoice_data': invoice_data}
            else:
                _logger.error(f"Invoice with sequence number {sequence_number} not found")
                return {'success': False, 'message': 'Invoice not found'}
        else:
            _logger.error("No sequence number provided")
            return {'success': False, 'message': 'No sequence number provided'}

