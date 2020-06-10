# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007-2008 Corvus Latinoamerica (http://corvus.com.ve) All Rights Reserved.
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



#parameters_seller:---------------------------------------------------------------------------------
#Parametros del Vendedor: se usan para hacer el calculo de las comisiones
#

class parameters_seller(osv.osv): 
    _name = 'parameters.seller'
    _description = 'Parameters Seller'	
    _columns = {
        'name': fields.char('Description', size=200, required=True),
        'quota_amount': fields.float('Quota Amount', digits=(16, int(config['price_accuracy']))),
        'quota_qty': fields.float('Quota Quantity', digits=(16, int(config['price_accuracy']))),
        'min': fields.float('Min', digits=(16, int(config['price_accuracy']))),
        'max': fields.float('Max', digits=(16, int(config['price_accuracy']))), 	
        'categ_salesman_id': fields.many2one('product.category.salesman', 'Product Category Salesman'),
        'seller_id': fields.many2one('res.partner', 'Seller Ref', ondelete='cascade'),
        'parameter_zone_id': fields.many2one('parameters.seller.zone', 'Parameters Ref'),
    }
    _defaults = { }

    def category_onchange(self, cr, uid, ids,category_id):
        res = {}
        if not  category_id:
            return {}
        categ = self.pool.get('product.category.salesman').read(cr, uid, [category_id], ['description'])
        if categ and categ[0]:
            res = {'value': {'name':categ[0]['description']}}
        return res
parameters_seller()  
