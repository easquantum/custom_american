# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Corvus Latinoamerica (http://corvus.com.ve) All Rights Reserved.
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
import os
from osv import fields,osv,orm
import mx.DateTime
import pooler 



#parameters_seller:--------------------------------------------------------------------------------
#Parametros de la Zona del Vendedor: Tabla maestra que se usan para hacer el calculo de las comisiones
#

class parameters_seller_zone(osv.osv): 
    _name = 'parameters.seller.zone'
    _description = 'Parameters Seller Zone'	
    _columns = {
        'name': fields.char('Description', size=200),
        'amount_cash': fields.float('Amount Cash Base', digits=(16, int(config['price_accuracy']))),
        'amount_total': fields.float('Amount Total Base', digits=(16, int(config['price_accuracy']))),
        'value_cash': fields.float('Value Cash', digits=(16, int(config['price_accuracy']))),
        'value_total': fields.float('Value Total', digits=(16, int(config['price_accuracy']))),
        'percent_min': fields.float('Percentage Min', digits=(16, int(config['price_accuracy']))),
        'percent_max': fields.float('Percentage Max', digits=(16, int(config['price_accuracy']))),
        'seller_id': fields.many2one('res.partner', 'Seller ref'),
        'zone_id': fields.many2one('res.partner.zone', 'Seller Zone', required=True),
        'year_id': fields.many2one('sale.commissionsyear', 'Year Period', required=True),
        #'period_id': fields.many2one('sale.commissionsperiod', 'Period', required=True),
        'active': fields.boolean('Activo'),
        'parameters_line': fields.one2many('parameters.seller', 'parameter_zone_id', 'Parameters Lines'),
    }
    _defaults = {
        'active': lambda *a: True,
     }

    def button_assigned_groups(self, cr, uid, ids, context={}):
        #parameters_groups_config.xml:
        #Archivo XML para obtener los parametros de los montos.
        ruta = os.getcwd()+'/addons/custom_american/custom_partner/'
        file = open(ruta+'parameters_groups_config.xml','r')
        data = file.read().split("\n")
        file.close()
        amount = 0
        pmin = 0
        pmax = 0
        for l in data:
            if  l.rfind('parameter') > 0:
                if l.rfind('quota_amount') > 0 and l.rfind('value') > 0:
                    qt = l[l.rfind('value')+7:-3]
                    amount = int(qt)
                if l.rfind('min') > 0 and l.rfind('value') > 0:
                    pmn = l[l.rfind('value')+7:-3]
                    pmin = int(pmn)
                if l.rfind('max') > 0 and l.rfind('value') > 0:
                    pmx = l[l.rfind('value')+7:-3]
                    pmax = int(pmx)
        #print amount,"  ",pmin,"  ",pmax
        sql = "SELECT id,description FROM product_category_salesman ORDER BY id"
        cr.execute (sql)
        vals = {}
        resultSQL = cr.fetchall()
        for ctg in resultSQL:
            vals = {'parameters_line':[(0,0,{
            'categ_salesman_id':ctg[0],
            'name': ctg[1] ,
            'quota_amount':amount ,
            'min': pmin ,
            'max': pmax ,
            'quota_qty':0})]
            }
            self.pool.get('parameters.seller.zone').write(cr, uid, ids, vals)
        return True

	#write:----------------------------------------------------------------------------------------
	#Se sobrescribe el metodo para registrale al vendedor la zona a la que fue asignado.
	#	
    def write(self, cr, uid, ids, vals, context=None):
        if ids:
            if vals.has_key('seller_id') and vals['seller_id']:
                parameters = self.browse(cr, uid, ids)[0]
                salesman_id = pooler.get_pool(cr.dbname).get('res.partner').search(cr,uid, [('code_zone_id','=',parameters.zone_id.id),('salesman','=',1)])
                #Si hay un vendedor para la zona, se le anula.
                if salesman_id:
                    cr.execute('UPDATE res_partner SET code_zone_id=NULL WHERE id = %d;'%salesman_id[0])
                #Se asigna la zona al vendedor seleccionado 
                cr.execute('UPDATE res_partner SET code_zone_id=%d WHERE id = %d;'%(parameters.zone_id.id,vals['seller_id'])) 
        return super(parameters_seller_zone, self).write(cr, uid, ids, vals,context=context)

parameters_seller_zone()  