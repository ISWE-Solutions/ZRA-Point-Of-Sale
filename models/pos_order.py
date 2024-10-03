from odoo import models, fields, api
import logging
import requests
from threading import Thread

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    invoice_created = fields.Boolean(string="Invoice Created", default=False)

    def create_invoices_for_orders(self):
        """Iterate over all orders and create invoices for each, only if the invoice hasn't been created yet."""
        _logger.info(f"Creating invoices for orders in session {self.session_id.name}")

        # Use a dummy "Walk-In Customer" if no specific customer is found
        dummy_customer = self.env['res.partner'].search([('name', '=', 'Walk-In Customer')], limit=1)
        if not dummy_customer:
            _logger.info(f"Creating dummy customer")
            dummy_customer = self.env['res.partner'].create({
                'name': 'Walk-In Customer',
                'customer_rank': 1,
            })

        invoices = []
        for order in self:
            try:
                # Check if invoice has already been created
                if order.invoice_created:
                    _logger.info(f"Invoice already created for order {order.name}, skipping...")
                    continue

                partner_id = order.partner_id.id if order.partner_id else dummy_customer.id
                _logger.info(f"Creating invoice for order {order.name} with partner {partner_id}")

                # Create the invoice
                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': partner_id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'price_unit': line.price_unit,
                    }) for line in order.lines],
                    'invoice_origin': order.name,
                })
                invoices.append(invoice)

                # Post the invoice
                invoice.action_post()
                _logger.info(f"Invoice {invoice.id} posted for order {order.name}")

                # Mark the order as invoiced
                order.invoice_created = True

                # Use Odoo's async process or cron for API payload
                # Execute synchronously to ensure transaction safety
                # self._send_invoice_payloads(invoice)

            except Exception as e:
                _logger.error(f"Error creating invoice for order {order.name}: {str(e)}")

        return invoices

    def _send_invoice_payloads(self, invoice):
        """Send payloads for the invoice to external APIs."""
        try:
            _logger.info(f"Sending payloads for invoice {invoice.id}")
            sales_payload = invoice.generate_sales_payload()
            stock_payload = invoice.generate_stock_payload()

            self._post_to_api("http://localhost:5000/trnsSales/saveSales", sales_payload, "Save Sales API Response")
            self._post_to_api("http://localhost:5000/trnsStock/saveStock", stock_payload, "Save Stock API Response")
        except Exception as e:
            _logger.error(f"Failed to send payloads for invoice {invoice.id}: {e}")

    def _post_to_api(self, url, payload, log_message):
        """Post the payload to an external API."""
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            _logger.info(f"{log_message}: {response.json()}")
        except requests.RequestException as e:
            _logger.error(f"API call to {url} failed: {e}")

    def get_invoice_for_order(self):
        """Retrieve the posted invoice associated with the order."""
        if not self.invoice_created:
            raise ValueError(f"No invoice has been created for the order {self.name}.")

        # Retrieve the invoice from account.move based on the order name (invoice_origin)
        invoice = self.env['account.move'].search(
            [('invoice_origin', '=', self.name), ('move_type', '=', 'out_invoice')], limit=1)

        if not invoice:
            raise ValueError(f"Invoice for the order {self.name} not found in account.move.")

        return invoice
