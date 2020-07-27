# -*- coding: utf-8 -*-
from odoo import http

# class ItemComponent(http.Controller):
#     @http.route('/item_component/item_component/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/item_component/item_component/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('item_component.listing', {
#             'root': '/item_component/item_component',
#             'objects': http.request.env['item_component.item_component'].search([]),
#         })

#     @http.route('/item_component/item_component/objects/<model("item_component.item_component"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('item_component.object', {
#             'object': obj
#         })