from odoo import models, api, fields
import logging
from odoo.exceptions import UserError
import requests
from threading import Thread

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _create_account_move(self, balancing_account=None, amount_to_balance=None, bank_payment_method_diffs=None):
        res = super(PosSession, self)._create_account_move(balancing_account, amount_to_balance,
                                                           bank_payment_method_diffs)
        self._create_invoices_for_orders()
        self._send_payloads_for_invoices()

        return res

    def _create_invoices_for_orders(self):
        dummy_customer = self.env['res.partner'].search([('name', '=', 'Walk-In Customer')], limit=1)
        if not dummy_customer:
            dummy_customer = self.env['res.partner'].create({
                'name': 'Walk-In Customer',
                'customer_rank': 1,
            })

        invoices = []
        for order in self.order_ids:
            partner_id = order.partner_id.id if order.partner_id else dummy_customer.id
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.qty,
                    'price_unit': line.price_unit,
                }) for line in order.lines],
            })
            invoices.append(invoice)

        # Post each invoice individually
        for invoice in invoices:
            invoice.action_post()

    def _send_payloads_for_invoices(self):
        invoices = self.env['account.move'].search([('invoice_origin', 'in', self.order_ids.mapped('name'))])
        for invoice in invoices:
            Thread(target=self._post_invoice_payload, args=(invoice,)).start()

    def _post_invoice_payload(self, invoice):
        sales_payload = invoice.generate_sales_payload()
        stock_payload = invoice.generate_stock_payload()

        # Post payloads to APIs
        self._post_to_api("http://localhost:8085/trnsSales/saveSales", sales_payload,
                          "Save Sales API Response resultMsg")
        self._post_to_api("http://localhost:8085/trnsStock/saveStock", stock_payload,
                          "Save Stock API Response resultMsg")

    def _post_to_api(self, url, payload, log_message):
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            _logger.info(f"{log_message}: {response.json()}")
        except requests.RequestException as e:
            _logger.error(f"API call failed: {e}")


class PosConfig(models.Model):
    _inherit = 'pos.config'

    stock_location_id = fields.Many2one(
        'stock.location',
        string='Stock Location',
        help="The stock location where products are stored"
    )
