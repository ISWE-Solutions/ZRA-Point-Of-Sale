from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PosInvoiceController(http.Controller):

    @http.route('/your/custom/route', type='json', auth="user", methods=['POST'])
    def create_invoices(self):
        _logger.info("Received request for creating invoices")
        params = request.params
        order_id = params.get('order_id')

        if order_id:
            order = request.env['pos.order'].browse(order_id)
            _logger.info(f"Processing single order: {order_id}")
            if order:
                invoices = order.create_invoices_for_orders()
                sequence_number = invoices[0].sequence_number if invoices else None
                _logger.info(f"Sequence number of the created invoice: {sequence_number}")
                _logger.info(f"Number of invoices created for order {order_id}: {len(invoices)}")
                return {'success': True, 'message': 'Invoice created and posted for order',
                        'sequence_number': sequence_number}
            else:
                _logger.error(f"Order with ID {order_id} not found")
                return {'success': False, 'message': 'Order not found'}
        else:
            session = request.env['pos.session'].search([('state', '=', 'opened')], limit=1)
            if session:
                _logger.info(f"Processing all orders in session {session.name}")
                orders = session.order_ids
                _logger.info(f"Number of orders in session {session.name}: {len(orders)}")

                invoices = orders.create_invoices_for_orders()
                sequence_number = invoices[0].sequence_number if invoices else None
                _logger.info(f"Sequence number of the created invoice: {sequence_number}")
                _logger.info(f"Total number of invoices created: {len(invoices)}")

                return {'success': True, 'message': 'Invoices created and posted for all orders',
                        'sequence_number': sequence_number}
            else:
                _logger.error("No active session found")
                return {'success': False, 'message': 'No active POS session found'}
