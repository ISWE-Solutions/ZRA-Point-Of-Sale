# -*- coding: utf-8 -*-
# from odoo import http


# class ZraPos(http.Controller):
#     @http.route('/zra_pos/zra_pos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zra_pos/zra_pos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('zra_pos.listing', {
#             'root': '/zra_pos/zra_pos',
#             'objects': http.request.env['zra_pos.zra_pos'].search([]),
#         })

#     @http.route('/zra_pos/zra_pos/objects/<model("zra_pos.zra_pos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zra_pos.object', {
#             'object': obj
#         })

