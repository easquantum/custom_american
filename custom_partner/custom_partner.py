# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 - 2009 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved
#                   
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs 
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company 
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
import tools
from tools import config
from osv import fields,osv,orm
import mx.DateTime
import pooler 


class res_partner_type(osv.osv): 
	_name = 'res.partner.type' 
	_description = 'Partners Type'	
	_columns = {
		'name': fields.char('Description', size=64, required=True),
		'code_type': fields.char('Code tipe', size=20, required=True),	
	}
	_defaults = {}
res_partner_type()

class res_partner_zone(osv.osv): 
	_name = 'res.partner.zone'
	_description = 'Partners Zone'	
	_columns = {
		'name': fields.char('Description', size=64, required=True),
		'code_zone': fields.char('Code Zone', size=20, required=True),	
		'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'), 
		'parent_id': fields.many2one('res.partner.zone','Parent Zone'),
		'type': fields.selection([('division','Division'),('territory','Territorio'),('zone','Zona'),],'Type',select=True), 
	}
	_defaults = {
	    'type': lambda *a: 'zone',
	}
res_partner_zone()

class res_partner(osv.osv):
	_inherit = "res.partner" 
	_columns = {  
		'code_zone_id': fields.many2one('res.partner.zone', 'Code Zone'),
		'code_type_id': fields.many2one('res.partner.type', 'Code Type'), 
		'nit': fields.char('Nit', size=15),
		'retention': fields.float(string='Retencion'),
		'adv_cos': fields.boolean('Costo ADV'),
        'salesman': fields.boolean('Salesman'),
        'carrier': fields.boolean('Carrier'),
        'special': fields.boolean('Contribuyente ISLR'),
        'pay_taxes': fields.boolean('Pay taxes'),
        'amount_cash': fields.float('Amount Cash Base', digits=(16, int(config['price_accuracy']))),
        'amount_total': fields.float('Amount Total Base', digits=(16, int(config['price_accuracy']))),
        'value_cash': fields.float('Value Cash', digits=(16, int(config['price_accuracy']))),
        'value_total': fields.float('Value Total', digits=(16, int(config['price_accuracy']))),
        'percent_min': fields.float('Percentage Min', digits=(16, int(config['price_accuracy']))),
        'percent_max': fields.float('Percentage Max', digits=(16, int(config['price_accuracy']))),
        'parameters_line': fields.one2many('parameters.seller', 'seller_id', 'Paramerts Lines'),
        'deductions_line': fields.one2many('deductions.assigned.seller', 'seller_id', 'Deductions Lines'),
        'islr': fields.boolean('Islr'),
        'person_type_id': fields.many2one('account.islr.person.type','Person Types Islr'),
        'not_contributor': fields.boolean('Not Contributor'),
	'property_account_reserv': fields.property(
			'account.account',
			type='many2one',
			relation='account.account',
			string="Reserva Account",
			method=True,
			view_load=True,
			help="This account will be used to value reserv for the current product category"),
        'property_retention_payable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Retention Payable",
            method=True,
            view_load=True,
            domain="[('type', '=', 'payable')]",
            help="This account will be used instead of the default one as the payable account for the current partner"),
        'property_retention_receivable': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Retention Receivable",
            method=True,
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="This account will be used instead of the default one as the receivable account for the current partner"),

	}
	_defaults = { 
		'adv_cos': lambda *a: 0,	
		'pay_taxes': lambda *a: True,
		'islr': lambda *a: False,
		'not_contributor': lambda *a: False,
	} 

	def button_assigned_groups(self, cr, uid, ids, context={}):
    		#Objeto Catregorias comisiones
	    	sql = "SELECT id,description FROM product_category_salesman ORDER BY id"
    		cr.execute (sql)
    		vals = {}
	    	resultSQL = cr.fetchall()
    		for ctg in resultSQL:
        		vals = {'parameters_line':[(0,0,{
        		    'categ_salesman_id':ctg[0],
        		    'name': ctg[1] ,
        		    'quota_amount':50 ,
        		    'min':50 ,
        		    'max':400 ,
        		    'quota_qty':0})]
        		    }
                	self.pool.get('res.partner').write(cr, uid, ids, vals)

	def name_get(self, cr, user, ids, context={}):
		if not len(ids):
			return []
		def _name_get(d):
			name = d.get('name','')
			code = d.get('ref',False)
			if code:
				name = '[%s] %s' % (code,name)
			return (d['id'], name)
		result = map(_name_get, self.read(cr, user, ids, ['name','ref'], context))
		return result

res_partner()

class res_partner_address(osv.osv):
	_inherit = "res.partner.address" 
	_columns = {  		
        	'city_id': fields.many2one("res.state.city", 'City', domain="[('state_id','=',state_id)]"),	
	}
	_defaults = { 	
	}

	def name_get(self, cr, user, ids, context={}):
		if not len(ids):
			return []
		res = []
		for r in self.read(cr, user, ids, ['name','zip','city','partner_id', 'street']):
		    if context.get('contact_display', 'contact')=='partner' and r['partner_id']:
		        res.append((r['id'], r['partner_id'][1]))
		    else:
		        addr = r['name'] or ''
		        if r['name'] and (r['zip'] or r['city']):
		            addr += ', '
		        addr += (r['street'] or '') + ' ' + (r['zip'] or '') + ' ' + (r['city'] or '')
		        res.append((r['id'], addr.strip() or '/'))
		return res
res_partner_address()
