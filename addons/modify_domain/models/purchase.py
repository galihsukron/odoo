# -*- coding: utf-8 -*-

from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[("new_state", "New State")])
