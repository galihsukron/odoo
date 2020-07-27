# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning
from datetime import datetime, timedelta

class masterComponent(models.Model):
    _name        = "master.component"
    _description = "Master Components"
 
    name                = fields.Char(string = "Component Name")
    estimation          = fields.Integer(string = "Estimation")
    
    

class itemItem(models.Model):
    _name        = "master.item"
    _description = "Master Items"
    
    name                = fields.Char(string = "Item Name")
    expected_date       = fields.Date(string = "Expected Date", compute="_compute_expected_date", store=True)
    start_date          = fields.Date(default = datetime.now().date(),string="Start Date")
    finish_date         = fields.Date(string = "Finish Date")
    component_ids       = fields.One2many("component.item","item_id", string="Component ID")
    total_percentage    = fields.Float(compute="_compute_total_percentage",string ="Total Percentage", store=True)
    total_estimation    = fields.Integer(compute="_compute_total_estimation",string="Total Estimation", store=True)
    stage_item          = fields.Selection([("draft","Draft"),("ongoing","Proses"),("done","Selesai")],default="draft", string="Stage")
    
    
    
    
    @api.model
    def create(self,vals):                   
        res =  super(itemItem,self).create(vals)
        total_percentage = 0
        for component in res.component_ids : 
            total_percentage += component.percentage                
        if total_percentage >= 0 and total_percentage <= 100 :
            pass
        else:
            raise Warning ("Oops, Total Persentase tidak boleh melebihi 100%")       
        return res
    
    
    @api.multi
    def write(self,vals):                         
        if "component_ids" in vals:
            total_percentage = 0
            for component in self.component_ids :
                percentage = component.percentage                
                for compo in vals["component_ids"]:                    
                    if compo[1] == component.id and compo[2] != False :
                        if "percentage" in compo[2]:
                            percentage= compo[2]["percentage"]
                total_percentage += percentage                                        
            if total_percentage >= 0 and total_percentage <= 100 :
                pass
            else:
                raise Warning ("Oops, Total Persentase tidak boleh melebihi 100%")       
        return super(itemItem,self).write(vals)
        
     
    @api.depends("component_ids.percentage")
    def _compute_total_percentage(self):        
        for record in self :
            percentage = 0 
            for component in record.component_ids :
                percentage += component.percentage
            record.total_percentage = percentage
            
    
    @api.depends("component_ids.component_estimation")
    def _compute_total_estimation(self):
        for record in self :
            estimation = 0 
            for component in record.component_ids :
                estimation += component.component_estimation
            record.total_estimation = estimation
            
                        
    @api.depends("start_date","component_ids")
    def _compute_expected_date(self):        
        for record in self :
            estimation = 0            
            for component in record.component_ids:
                estimation += component.component_id.estimation                                  
            record.expected_date  = datetime.strptime(str(record.start_date),"%Y-%m-%d") + timedelta(days=int(estimation)) 

    
    
class componentItem(models.Model):
    _name        = "component.item"
    _description = "Component Item"
    
    component_id        = fields.Many2one("master.component", string="Component ID")
    item_id             = fields.Many2one("master.item", string="Item ID")
    percentage          = fields.Float(string="Percentage")
    component_estimation= fields.Integer(related="component_id.estimation", string="Component Estimation")
    component_name      = fields.Char(related="component_id.name", string="Component Name")
    
