
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import fields, models, api
from openerp import tools


class project_issue_report(models.Model):
    _name = "asset.distribution.report"
    _auto = False

    asset_id = fields.Many2one('asset.asset','Asset')
    type_id = fields.Many2one('asset.type','Type')
    location_id = fields.Many2one('asset.location','Location')

    #team_id = fields.Many2one('crm.team', 'Sale Team', oldname='section_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    #opening_date = fields.Datetime('Date of Opening', readonly=True)
    #create_date = fields.Datetime('Create Date', readonly=True)
    inspection_date = fields.Datetime('Date of Closing', readonly=True)
    #date_last_stage_update = fields.Datetime('Last Stage Update', readonly=True)
    #stage_id = fields.Many2one('project.task.type', 'Stage')
    nbr = fields.Integer('# of Asset', readonly=True)  # TDE FIXME master: rename into nbr_issues
    #working_hours_open = fields.Float('Avg. Working Hours to Open', readonly=True, group_operator="avg")
    #working_hours_close = fields.Float('Avg. Working Hours to Close', readonly=True, group_operator="avg")
    #delay_open = fields.Float('Avg. Delay to Open', digits=(16,2), readonly=True, group_operator="avg",
        #                               help="Number of Days to open the project issue.")
    #delay_close = fields.Float('Avg. Delay to Close', digits=(16,2), readonly=True, group_operator="avg",
        #                               help="Number of Days to close the project issue")
    #company_id = fields.Many2one('res.company', 'Company')
    #priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    #project_id = fields.Many2one('project.project', 'Project',readonly=True)
    log_pic = fields.Many2one('res.users', 'Inspect by',readonly=True)
    #partner_id = fields.Many2one('res.partner','Contact')
    #channel = fields.Char('Channel', readonly=True, help="Communication Channel.")
    #task_id = fields.Many2one('project.task', 'Task')
    #email = fields.Integer('# Emails', size=128, readonly=True)

    #@api.model_cr
    #def init(self):
    #    tools.drop_view_if_exists(self._cr, 'asset_distribution_report')
    #    self._cr.execute("""
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'asset_distribution_report')
        cr.execute("""        
            CREATE OR REPLACE VIEW asset_distribution_report AS (
                SELECT --a.name, l.name, t.name,
                    a.id, 
                    a.id as asset_id,
                    l.id as location_id, 
                    t.id as type_id,
                    a.log_pic,
                    a.company_id,
                    date(a.log_date) as inspection_date,
                    1 as nbr 
                     
                from asset_asset a 
                inner join asset_type t on a.type_id = t.id
                inner join asset_location l on a.log_location = l.id
                --inner join asset_move m on m.asset_id = a.id
            )""")
