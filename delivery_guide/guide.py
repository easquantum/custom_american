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
from osv import fields,osv,orm
from tools import config
import mx.DateTime
import pooler

class delivery_guide(osv.osv):
    _name = "delivery.guide"
    _description = "Delivery Guide"
    _columns = {
        'name': fields.char('Delivery Guide', size=64, required=True, readonly=True),
        'carrier_company_id': fields.many2one('res.partner', 'Carrier Company', required=True, states={'done':[('readonly',True)]}),
        'date_guide':fields.date('Date Guide', states={'done':[('readonly',True)]}),
        'driver_id': fields.many2one('res.partner', 'Driver', required=True, states={'done':[('readonly',True)]}),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'ruta_id': fields.many2one('guide.ruta', 'Ruta', states={'done':[('readonly',True)]}),
        'vehiculo_id': fields.many2one('guide.vehiculo', 'Vehiculo Carga'),
        'guide_line': fields.one2many('delivery.guide.line', 'guide_id', 'Invoice Lines', states={'done':[('readonly',True)]}),
        'guide_picking': fields.one2many('delivery.guide.picking.line', 'guide_id', 'Picking Lines', states={'done':[('readonly',True)]}), 
        'state': fields.selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Guide State', readonly=True, select=True),
        'weight': fields.float('Peso Bruto'),
        'weight_vehiculo': fields.float('Peso Vehiculo'),
        'traspaso': fields.boolean('Traspaso', states={'done':[('readonly',True)]}),
        'printed': fields.boolean('Impresa' ),
        'paid': fields.boolean('Pagada' ),
    }
    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('delivery.guide').guide_seq_get(cr, uid),
        'date_guide': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'traspaso': lambda *a: False,
        'printed': lambda *a: False,
        'paid': lambda *a: False,
    }

    def guide_seq_get(self, cr, uid):
        pgp_obj = self.pool.get('period.generalperiod')
        pgp_ids = pgp_obj.find(cr, uid, tp='sale')
        pg = pgp_obj.browse(cr, uid, pgp_ids)[0]
        to_update = {'suffix':'-'+pg.code}
        pool_seq=self.pool.get('ir.sequence')
        cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='delivery.guide' and active=True")
        res = cr.dictfetchone()
        res.update(to_update)
        if res:
            if res['number_next']:
                return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
            else:
                return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
        return False

    def create(self, cursor, user, vals, context=None):
        gnro =self.pool.get('ir.sequence').get(cursor, user, 'delivery.guide')
        pgp_obj = self.pool.get('period.generalperiod')
        pgp_ids = pgp_obj.find(cursor, user, tp='sale')
        pg = pgp_obj.browse(cursor, user, pgp_ids)[0]
        vals['name']=gnro+'-'+pg.code
        #print 'CASO UNICO - creando guia despacho'
        dg_id=super(delivery_guide, self).create(cursor, user, vals,context=context)
        dg_line=[]
        if 'guide_line' in vals:
            dg_line = vals['guide_line']
            for lineas in dg_line:
                #print '********** CASO ---  CREAR ENLACE FACTURA ************'
                if 'invoice_id' in lineas[2]:						
                    self.pool.get('account.invoice').write(cursor, user, [lineas[2]['invoice_id']], {'guide_id':dg_id})
        return dg_id

    def write(self, cursor, user, ids, vals, context=None):		
        dg_line=[]
        obj_guide    = pooler.get_pool(cursor.dbname).get('delivery.guide')
        datosguia    = obj_guide.browse(cursor, user, ids[0])
        if 'guide_line' in vals and not datosguia.traspaso:
            dg_line = vals['guide_line']
            for lineas in dg_line:
                if lineas[0]==0:
                    #print '********** CASO 2-1  CREAR ENLACE FACTURA ************'
                    if 'invoice_id' in lineas[2]:
                        self.pool.get('account.invoice').write(cursor, user, [lineas[2]['invoice_id']], {'guide_id':ids[0]})
                elif lineas[0]==1:
                    #print '********** CASO 2-2  MODIFICAR ENLACE FACTURA ************'
                    if 'invoice_id' in lineas[2]:
                        inv_id = self.pool.get('delivery.guide.line').read(cursor, user, [lineas[1]], ['invoice_id'])[0]['invoice_id'][0]
                        self.pool.get('account.invoice').write(cursor, user, [inv_id], {'guide_id':False})
                        self.pool.get('account.invoice').write(cursor, user, [lineas[2]['invoice_id']], {'guide_id':ids[0]})					
                elif lineas[0]==2:
                    #print '********** CASO 2-3  ELIMINAR ENLACE FACTURA ************'
                    inv_id = self.pool.get('delivery.guide.line').read(cursor, user, [lineas[1]], ['invoice_id'])[0]['invoice_id'][0]						
                    self.pool.get('account.invoice').write(cursor, user, [inv_id], {'guide_id':False})
                else:
                    print 'ERROR AL ENLAZAR LA FACTURA'
        if not datosguia.traspaso:
            vals['guide_picking'] = []
        return super(delivery_guide, self).write(cursor, user, ids, vals,context=context)

    def unlink(self, cr, uid, ids, context={}, check=True):	
        toremove = []
        toremove = self.pool.get('delivery.guide').read(cr, uid, ids, ['guide_line'])[0]['guide_line']		
        for dg_lin_id in toremove:
            #print '********** CASO ---  ELIMINAR ENLACE FACTURA ************'
            inv_id = self.pool.get('delivery.guide.line').read(cr, uid, [dg_lin_id], ['invoice_id'])[0]['invoice_id'][0]		
            self.pool.get('account.invoice').write(cr, uid, [inv_id], {'guide_id':False})		
        result = super(delivery_guide, self).unlink(cr, uid, ids, context)
        return result

	##button_compute_weight----------------------------------------------------------------------------------------------------
	#Se Calcula el Peso de la Guia
	#
    def button_compute_weight(self, cr, uid, ids, context={}):
        if not ids:
            return False
        total_peso	= 0	
        peso        = 0
        obj_guide    = pooler.get_pool(cr.dbname).get('delivery.guide')        
        guia    = obj_guide.browse(cr, uid, ids[0])
        if guia.vehiculo_id:
            peso = self.pool.get('guide.vehiculo').read(cr, uid, [guia.vehiculo_id.id], ['weight'])[0]['weight']
        if not guia.traspaso:
            for invoice in guia.guide_line:
                for invoice_line in invoice.invoice_id.invoice_line:
                    total = 0
                    if invoice_line.quantity and invoice_line.product_id.weight_net:
                        total    = invoice_line.quantity * invoice_line.product_id.weight_net
                    total_peso += total
        if guia.traspaso:
            for picking in guia.guide_picking:
                for picking_line in picking.picking_id.move_lines:
                    total = 0
                    if picking_line.product_qty and picking_line.product_id.weight_net:
                        total = picking_line.product_qty * picking_line.product_id.weight_net
                    total_peso += total
        if total_peso:
            self.pool.get('delivery.guide').write(cr, uid, ids, {'weight': total_peso,'weight_vehiculo':peso})
        #if total_peso > peso: 
        #    return {'warning': {'title':'Error','message':'El peso de la Carga es mayor que el peso limite del vehiculo!!!'}} 
        return True
	##vehiculo_id_change----------------------------------------------------------------------------------------------------
	#obtiene el peso del vehiculo
	#
    def vehiculo_id_change(self, cr, uid, ids,vehiculo_id):
        if not vehiculo_id:
            return {}
        peso = self.pool.get('guide.vehiculo').read(cr, uid, [vehiculo_id], ['weight'])[0]['weight']
        res = {'value': {'weight_vehiculo':peso}}
        return res
delivery_guide()

#delivery_guide_line--------------------------------------------------------------------------------------------------
#Facturas asociadas a la guia de despacho
class delivery_guide_line(osv.osv):
    _name = 'delivery.guide.line'
    _description = 'Delivery Guide line'	
    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True),
        'guide_id': fields.many2one('delivery.guide', 'Guide Ref', ondelete='cascade'),		
    }
    _sql_constraints = [
        ('invoice_uniq', 'unique (invoice_id)', 'The invoice must be unique !')
    ]

    def guide_id_change(self, cr, uid, ids,invoice_id,traspaso):
        if not  invoice_id:
            return {}
        if  traspaso:
            return {'value': {'name':'','invoice_id':False}, 'warning': {'title':'Error','message':'La Guia es de tipo Traspaso'}}
        else:
            refe = self.pool.get('account.invoice').read(cr, uid, [invoice_id], ['reference'])[0]['reference']
            res = {'value': {'name':refe}}
            return res
delivery_guide_line()

#delivery_guide_picking_line--------------------------------------------------------------------------------------------------
#Notas de Salida asociadas a la guia de despacho
class delivery_guide_picking_line(osv.osv):
    _name = 'delivery.guide.picking.line'
    _description = 'Delivery Guide Picking line'	
    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'picking_id': fields.many2one('stock.picking', 'Piking', required=True),
        'guide_id': fields.many2one('delivery.guide', 'Guide Ref', ondelete='cascade'),		
    }
    _sql_constraints = [
        ('guide_picking_uniq', 'unique (picking_id)', 'The picking must be unique !')
    ]

    def picking_id_change(self, cr, uid, ids,picking_id,traspaso):
        if not picking_id:
            return {}
        if not traspaso:
            return {'value': {'name':'','guide_id':False}, 'warning': {'title':'Error','message':'La Guia no es de tipo Traspaso'}}
        else:
            nomb = self.pool.get('stock.picking').read(cr, uid, [picking_id], ['name'])[0]['name']
            res = {'value': {'name':nomb}}
            return res		
delivery_guide_picking_line()

#account_invoice----------------------------------------------------------------------------------------------------------------------
#Se agrega a la tabla account_invoice el campo: 
#
#1.- 'guide_id': este campo permite establecer la relacion entre las guias de despacho y las facturas.   
#
#-------------------------------------------------------------------------------------------------------------------------------------
class account_invoice(osv.osv):
    _inherit = "account.invoice"
    _columns = {
        'guide_id':fields.many2one("delivery.guide","Delivery Guide", help="Guide of Delivery"),
    }
account_invoice()
