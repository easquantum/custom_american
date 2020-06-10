# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2009 Corvus Latinoamerica (http://corvus.com.ve) All Rights Reserved.
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
##############################################################################

import time
import tools
from tools import config
from osv import fields,osv,orm
import mx.DateTime
import pooler 



#deductions_seller:---------------------------------------------------------------------------------
#Deducciones del Vendedor: 
#

class deductions_seller(osv.osv): 
	_name = 'deductions.seller'
	_description = 'Deductions Seller'	
	_columns = {
		'name': fields.char('Description', size=200, required=True),
		'code': fields.char('Code', size=8),
	}
	_defaults = { }
deductions_seller() 

#deductions_assigned_seller:---------------------------------------------------------------------------------
#Parametros del Vendedor: se usan para hacer el calculo de las comisiones
#

class deductions_assigned_seller(osv.osv): 
    _name = 'deductions.assigned.seller'
    _description = 'deductions Assigned Seller'	
    _columns = {
        'name': fields.char('Description', size=200, required=True),
        'amount_total': fields.float('Amount Total', digits=(16, int(config['price_accuracy']))),
        'percent': fields.float('Percentage', digits=(16, int(config['price_accuracy']))),
        'deduction_id': fields.many2one('deductions.seller', 'Deduction Seller'),
        'seller_id': fields.many2one('res.partner', 'Seller Ref', ondelete='cascade'),
    }
    _defaults = { }
    
    
    ##deduction_id_change--------------------------------------------------------------------------------------------
    def deduction_id_change(self, cr, uid, ids, deduction, context=None):
        vals   ={}
        if not deduction:
            return {'value':vals}
        resp = self.pool.get('deductions.seller').browse(cr, uid, deduction, context=context)
        vals['name'] = resp.name
        return {'value':vals}

deductions_assigned_seller()