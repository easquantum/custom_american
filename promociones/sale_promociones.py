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


import tools
from tools import config
from osv import fields,osv,orm
import pooler
import time

#------------------------------------------------------------------------
#Promociones de Ventas:
#------------------------------------------------------------------------

class sale_promocion(osv.osv): 
    ##amount_cal_total-----------------------------------------------------------------------------------------------
    #Se obtiene el total general
    # 
    def _amount_cal_total(self, cr, uid, ids, name, args, context=None):
        resp = {}
        for promo in self.browse(cr, uid, ids, context):
            resp[promo.id] = { 'total': 0.0}
            for line in promo.promocion_line:
                if line.price and line.quantity:
                    resp[promo.id]['total'] += line.price * line.quantity 
        return resp

    _name = 'sale.promocion'
    _description = 'Sale Promociones'	
    _columns = {
    	'name': fields.char('Nro. Promocion', size=64, readonly=True, required=True),
    	'date_promocion':fields.date('Fecha Promocion'),
    	'partner_id': fields.many2one('res.partner', 'Cliente', required=True),
    	'code_zone_id': fields.many2one('res.partner.zone', 'Zona'),
    	'type': fields.selection([
    	    ('promocion', 'Promocion'),
    	    ('regalo', 'Regalo')], 'Tipo'),
    	'state': fields.selection([
    	    ('draft', 'Draft'),
    	    ('confirmed', 'Confirmed'),
    	    ('done', 'Done'),
    	    ('cancel', 'Cancelled')], 'State', readonly=True, select=True),
    	'notes': fields.text('Notas'),
    	'promocion_line': fields.one2many('sale.promocion.line', 'promocion_id', 'Promocion Lines'),
    	'promocion_invoice_line': fields.one2many('sale.promocion.invoice.line', 'promocion_id', 'Promocion Invoice Lines'),
    	'total': fields.function(_amount_cal_total, method=True,  digits=(16,4), string='Total', store=True, multi='all'),
    }
    _defaults = {
        'date_promocion': lambda *a: time.strftime('%Y-%m-%d'),
        'name': lambda obj, cr, uid, context: obj.pool.get('sale.promocion').promocion_seq_get(cr, uid,context),
        'state': lambda *a:'draft',
    }

    ##promocion_seq_get-------------------------------------------------------------------------------------------------------
    #Asigna el numero de promocion, de forma temporal, al guardar se obtiene el definitivo
    #
    def promocion_seq_get(self, cr, uid, context=None):
        pool_seq=self.pool.get('ir.sequence')
        res = ''
        if context and context.has_key('type'):
            if context['type'] == 'promocion':
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='sale.promocion' and active=True")
                res = cr.dictfetchone()
            if context['type'] == 'regalo':
                cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='sale.promocion_regalo' and active=True")
                res = cr.dictfetchone()

        if res:
            if res['number_next']:
                return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
            else:
                return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
        return False	
    
    
    #Este porceso se llama cada vez que se crea una nueva promocion.	
    #Asigna el numero de promocion definitivo y aumenta el contador en la secuencia 'sale.promocion' 
    #
    def create(self, cr, user, vals, context=None):
        if context:
            if context.has_key('type') and context['type'] == 'promocion':
                vals['name'] = self.pool.get('ir.sequence').get(cr, user, 'sale.promocion')
                vals['type'] = 'promocion'
            if context.has_key('type') and context['type'] == 'regalo':
                vals['name']= self.pool.get('ir.sequence').get(cr, user, 'sale.promocion_regalo')
                vals['type']= 'regalo'
        return super(sale_promocion,self).create(cr, user, vals, context)

    #onchange_partner_id:---------------------------------------------------------------------------------------------------------
    #Se sobreescribe este metodo para asignar nuevos valores automaticamente, en el momento que se selecciona el cliente
    #	
    def onchange_partner_id(self, cr, uid, ids, partner):
        result = {}
        #Asignar Zona:
        #Se obtiene la zona del cliente y se asigna a la promocion
        if partner:
            zona_id = self.pool.get('res.partner').browse(cr, uid, partner).code_zone_id.id or False
            result = {'value': {'code_zone_id':zona_id}}
        return result
sale_promocion()

class sale_promocion_line(osv.osv):
    ##amount_cal_subtotal-----------------------------------------------------------------------------------------------
    #Se obtiene el sutotal del datelle
    # 
    def _amount_cal_subtotal(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] =  line.price * line.quantity
        return res

    _name = "sale.promocion.line"		
    _columns = {
        'promocion_id': fields.many2one('sale.promocion', 'Relacion promocion', ondelete='cascade'),
        'name': fields.char('Descripcion', size=200, required=True),
        'quantity': fields.integer('Cantidad'),
        'costo_price': fields.float('Costo', digits=(16, int(config['price_accuracy']))),
        'price': fields.float('Precio', digits=(16, int(config['price_accuracy']))),
        'subtotal': fields.function(_amount_cal_subtotal, method=True,  digits=(16, int(config['price_accuracy'])), string='SubTotal'),
        'product_id': fields.many2one('product.product', 'Producto', select=True),
        'concepto_id': fields.many2one('sale.concepto.promocion', 'Concepto', select=True),
        'note': fields.char('Observacion', size=240),
    }
    _defaults = {
        'quantity': lambda *a:1,
    }

    #onchange:---------------------------------------------------------------------------------------------------------
    #	
    def onchange_concept_id(self, cr, uid, ids, concepto):
        result = {}
        #Asignar el valor del concepto a la descripcion
        if concepto:
            nomb_concepto = self.pool.get('sale.concepto.promocion').browse(cr, uid, concepto).name or ''
            result = {'value': {'name':nomb_concepto}}
        return result

    #onchange:---------------------------------------------------------------------------------------------------------
    #	
    def onchange_product_id(self, cr, uid, ids, producto):
        result = {}
        #Asignar la descripcion del producto a la descripcion
        if producto:
            obj_producto = self.pool.get('product.product').browse(cr, uid, producto)
            if obj_producto:
                nomb = obj_producto.product_tmpl_id.name
                cod  = obj_producto.default_code
                prec = obj_producto.publ_price
                costo = obj_producto.price_extra
                result = {'value': {'name': '[ '+ cod +' ] ' + nomb,'price':prec,'costo_price':costo}}
        return result
sale_promocion_line()

class sale_promocion_invoice_line(osv.osv):
    _name = "sale.promocion.invoice.line"
    _columns = {
        'promocion_id': fields.many2one('sale.promocion', 'Relacion promocion', ondelete='cascade'),
        'name': fields.char('Descripcion', size=64),
        'invoice_id': fields.many2one('account.invoice', 'Factura', select=True),
        'date_invoice':fields.date('Fecha Factura'),
    }
    _defaults = {
    
    }
    _sql_constraints = [
        ('invoice_uniq', 'unique (invoice_id)', 'La Factura ya esta relacionada en una promocion')
    ]

    #onchange_invoice_id:---------------------------------------------------------------------------------------------------------
    #Asignar la fecha de la factura
    #	
    def onchange_invoice_id(self, cr, uid, ids, invoice):
        result = {}
        vals   = {}
        #Asignar Fecha:
        #Se obtiene la fecha de la factura y se asigna al detalle de la promocion (factura) 
        if invoice:
            sql = "select id from sale_promocion_invoice_line where invoice_id=%d"%invoice
            cr.execute(sql)
            res = cr.dictfetchone()
            if res and res['id']:
                raise osv.except_osv(_('Warning !'), _('Fatura Registrada en otra Promosion o Regalo'))
                vals = {'invoce_id':False}
            else:
                fecha = self.pool.get('account.invoice').browse(cr, uid, invoice).date_invoice or ''
                vals = {'date_invoice':fecha}
            result = {'value': vals }
        return result
sale_promocion_invoice_line()
