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

from mx import DateTime
import time
import netsvc
from osv import fields,osv
import ir
from tools import config
from tools.translate import _
import tools
from xml.dom import minidom
import pooler

#----------------------------------------------------------
# Custom Stock Location
#----------------------------------------------------------
class stock_location(osv.osv):
    _inherit = "stock.location"
    _columns = {
        'warehouse_id': fields.integer('Warehouse'),
    }
stock_location()


#----------------------------------------------------------
# Custom Stock Warehouse
#----------------------------------------------------------
class stock_warehouse(osv.osv):
    _inherit = "stock.warehouse"

    ##write-------------------------------------------------------------------------------------------------------
    #Asigna el id del almacen a las ubicaciones
    # Realizado por: Javier Duran
    # Fecha:06-06-09
    def write(self, cr, uid, ids, vals, context={}):
        loc_list = ['lot_input_id','lot_stock_id','lot_output_id']
        obj_loc = self.pool.get('stock.location')
        loc_ids = []
        loc = [v for v in vals if v in loc_list]        
        if loc:
            loc_ids = [vals[l] for l in loc]
            obj_loc.write(cr, uid, loc_ids, {'warehouse_id': ids[0]})
        return super(stock_warehouse, self).write(cr, uid, ids, vals, context)

    ##create-------------------------------------------------------------------------------------------------------
    #Asigna el id del almacen a las ubicaciones
    # Realizado por: Javier Duran
    # Fecha:06-06-09

    def create(self, cr, uid, vals, context={}):
        warehouse_id = super(stock_warehouse, self).create(cr, uid, vals, context)
        loc_list = ['lot_input_id','lot_stock_id','lot_output_id']
        obj_loc = self.pool.get('stock.location')
        loc_ids = []
        loc = [v for v in vals if v in loc_list]
        if loc:
            loc_ids = [vals[l] for l in loc]
            obj_loc.write(cr, uid, loc_ids, {'warehouse_id': warehouse_id})
        return warehouse_id

    ##name_search-----------------------------------------------------------------------------------------------------
    # Devuelve los ids de los almacenes cuando se realiza la busqueda
    # la cual esta sujeta al domain del campo
    # Realizado por: Javier Duran
    # Fecha:10-06-09

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}

        ids = []
        if len(args):
            where = ' and '.join(map(lambda x: ' '+x[1]+'\'%'+str(x[2])+'%\'',args))
            cr.execute("SELECT sw.id FROM stock_warehouse AS sw WHERE sw.name %s;"%where)
            res = cr.fetchall()
            ids = map(lambda tp:map(lambda elem:elem,tp)[0], res)
        if not len(ids):
            ids = self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context)
        return result


stock_warehouse()


#----------------------------------------------------------
# Custom Stock Picking
#----------------------------------------------------------
class stock_picking(osv.osv):
    _inherit = "stock.picking" 

    _columns = {
           'nota_atencion_ids': fields.many2many('nota.atencion', 'picking_nota_atencion_rel', 'picking_id', 'nota_atencion_id', 'Notas Atencion'),
           'code_zone_id': fields.many2one('res.partner.zone', 'Code Zone'),
        # Realizado por: Javier Duran
        # Fecha:06-06-09
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse'),
        'warehouse_dest_id': fields.many2one('stock.warehouse', 'Destination Warehouse'),
        'type': fields.selection([('out','Sending Goods'),('in','Getting Goods'),('internal','Internal'),('delivery','Delivery')], 'Shipping Type', required=True, select=False),
        'type2': fields.selection([('tras','Traspaso'),('mues','Muestreo'),('trans','Transferencia'),('dev','Devolucion'),('aju','Ajuste'),('def','Predeterminado')], 'Shipping SubType'),
        'backorder':fields.boolean('Backorder',readonly=True), 
        'date_cancel':fields.date('Date Cancel'),          
    }
    _defaults = {
        'name': lambda obj, cr, uid, context: obj.pool.get('stock.picking').picking_seq_get(cr, uid, context),
        'type':lambda *a: 'internal',
        'backorder':lambda *a: False,
        'type2':lambda *a: 'def',        
    }
    
    
    ##picking_seq_get--------------------------------------------------------------------------------------------
    # obtiene el correlativo de las notas (entradas, salidas e internas)
    # Realizado por: Javier Duran
    # Fecha:24-06-09

    def picking_seq_get(self, cr, uid, context):
        code = context['type'] + '_' + context['type2']
        pool_seq=self.pool.get('ir.sequence')
        cr.execute(("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='stock.picking.%s' and active=True") % (code, ))
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
            else:
                return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
        return False    
    #-------------------------------------------------------------------------------------------------------------------

    ##create------------------------------------------------------------------------------------------------------------
    #Este proceso se llama cada vez que se crea una nueva nota.    
    #Asigna el numero de nota definitivo y aumenta el contador en la secuencia 'stock.picking.tipo' 
    # Realizado por: Javier Duran
    # Fecha:25-06-09

    def create(self, cr, uid, vals, context=None):
        code = vals['type'] 
        if vals.has_key('type2') and vals['type2']:
            code += '_' + vals['type2']
        else:
            code += '_'+'def'
        name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.%s' % code)
        vals['name'] = name
        #Se Valida si el Picking es un movimiento a perdida
        if context and context.has_key('origin') and context['origin'] == 'LOST':
            vals['origin'] = 'LOST'
        return super(stock_picking,self).create(cr, uid, vals, context)        
    #-------------------------------------------------------------------------------------------------------------------        
    

    ##action_invoice_create------------------------------------------------------------------------------------------------------------
    #Se sobreescribe este proceso, para asignar los campos:    
    # 'name' : Nro de la compra a la Factura 
    # 'warehouse_id': Asignar el Almacen al que pertenece la factura
    # 'reference' :  Asignar la Nota de Entrada 
    def action_invoice_create(self, cursor, user, ids, journal_id=False,group=False, type='out_invoice', context=None):
        '''Return ids of created invoices for the pickings'''
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoices_group = {}
        res = {}
        for picking in self.browse(cursor, user, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            payment_term_id = False
            partner = picking.address_id and picking.address_id.partner_id
            if not partner:
                raise osv.except_osv(_('Error, no partner !'),_('Please put a partner on the picking list if you want to generate invoice.'))
            
            if type in ('out_invoice', 'out_refund'):
                account_id = partner.property_account_receivable.id
                payment_term_id=self._get_payment_term(cursor, user, picking)
            else:
                account_id = partner.property_account_payable.id
            
            address_contact_id, address_invoice_id = self._get_address_invoice(cursor, user, picking).values()
            
            comment = self._get_comment_invoice(cursor, user, picking)
            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice=invoice_obj.browse(cursor, user,invoice_id)
                invoice_vals = {
                        'name': invoice.name +', '+picking.name,
                        'origin': invoice.origin+', '+picking.name+(picking.origin and (':' + picking.origin) or ''),
                        'comment':(comment and (invoice.comment and invoice.comment+"\n"+comment or comment)) or (invoice.comment and invoice.comment or ''),
                }
                invoice_obj.write(cursor, user, [invoice_id],invoice_vals,context=context)
            else:
                invoice_vals = {
                        'name': picking.name,
                        'reference': picking.name,
                        'origin': picking.name + (picking.origin and (':' + picking.origin) or ''),
                        'type': type,
                        'account_id': account_id,
                        'partner_id': partner.id,
                        'address_invoice_id': address_invoice_id,
                        'address_contact_id': address_contact_id,
                        'comment': comment,
                        'payment_term': payment_term_id,
                        'fiscal_position': partner.property_account_position.id,
                }

                ##------------------------------------------------------------------------------
                #Modificado:  Corvus Latinoamerica
                #Fecha: 02-04-08
                # Asignarle almacen como nro de compra el mismo valor que tiene la nota de entrada
                if type == 'in_invoice': 
                    almacen_id = picking.purchase_id.warehouse_id.id
                    invoice_vals['warehouse_id'] =  almacen_id                
                    co = picking.name
                    co = co.replace("NE","CO")
                    invoice_vals['name'] = co
                    if partner.retention:
                        invoice_vals['p_ret'] = partner.retention
                    if partner.property_payment_term:
                        invoice_vals['payment_term'] = partner.property_payment_term.id
                    
                if type == 'out_invoice':
                    # Asignacion Nro Factura - Usando las secuencia de out
                    sale    = pooler.get_pool(cursor.dbname).get('sale.order').read(cursor, user, [picking.sale_id.id],['nota_atencion'])
                    if sale and sale[0]:
                        invoice_vals['nota_atencion'] = sale[0]['nota_atencion']
                    notas_ids = []
                    sql = "SELECT nota_atencion_id FROM sale_nota_atencion_rel WHERE sale_id=%d;"%picking.sale_id.id
                    cursor.execute (sql)
                    for nota in cursor.fetchall():
                        notas_ids.append(nota[0])
                        if notas_ids:
                            invoice_vals['nota_atencion_ids'] = [(6, 0, notas_ids)]
                    numero_factura = self.pool.get('ir.sequence').get(cursor, user, 'account.invoice.sales')
                    invoice_vals['name'] = numero_factura
                    invoice_vals['number'] = numero_factura
                    invoice_vals['reference'] = picking.origin
                    invoice_vals['origin'] = picking.name
                    invoice_vals['code_zone_id'] = picking.code_zone_id.id
                    almacen_id = picking.sale_id.shop_id.warehouse_id.id
                    #Asinacion de las Notas de Atencion
                    if almacen_id:
                        invoice_vals['warehouse_id'] =  almacen_id

                ##------------------------------------------------------------------------------    
                cur_id = self.get_currency_id(cursor, user, picking)
                if cur_id:
                    invoice_vals['currency_id'] = cur_id
                if journal_id:
                    invoice_vals['journal_id'] = journal_id
                invoice_id = invoice_obj.create(cursor, user, invoice_vals, context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            for move_line in picking.move_lines:
                ##-------------------------------------------------------------------------------------------------------
                #Modificado:  Corvus Latinoamerica
                #se obtiene la lista de precio correspondiente para el proveedor seleccionado
                priceclist_id = self.pool.get('res.partner').browse(cursor, user, partner.id).property_product_pricelist_purchase.id
                
                #Obtener costo standard  [price_std]  para ser almacenado el la linea de los productos de las compras. 
                #este campo es usado para obtener las reserva             
                #print "Price List",priceclist_id 
                prod = self.pool.get('product.product').read(cursor, user, [ move_line.product_id.id ], ['standard_price','cost_price','list_price','product_tmpl_id'])[0]
                if prod:
                    price_std  = prod['cost_price']
                    if type == 'in_invoice':
                        price_std  = prod['standard_price']
                    price_fact = prod['list_price']
                else:
                    price_std = 0.0
                    price_fact = 0.0
                ##-------------------------------------------------------------------------------------------------------    
                origin=move_line.picking_id.name
                if move_line.picking_id.origin:
                    origin+=':' + move_line.picking_id.origin
                if group:
                    name = picking.name + '-' + move_line.name
                else:
                    name = move_line.name
                
                if type in ('out_invoice', 'out_refund'):
                    account_id = move_line.product_id.product_tmpl_id.property_account_income.id
                    if not account_id:
                        account_id = move_line.product_id.categ_id.property_account_income_categ.id
                    if not partner.property_account_reserv.id:
                        account_res_id = account_id
                    else:
                        account_res_id = partner.property_account_reserv.id
                else:
                    account_id = move_line.product_id.product_tmpl_id.property_account_expense.id
                    # se agrego para buscar el id de la cuenta de reserva
                    account_res_id = partner.property_account_reserv.id
                    ##-------------------------------------------------------------------------------------------------
                    if not account_id:
                        account_id = move_line.product_id.categ_id.property_account_expense_categ.id
                
                price_unit = self._get_price_unit_invoice(cursor, user, move_line, type)
                discount = self._get_discount_invoice(cursor, user, move_line)
                tax_ids = self._get_taxes_invoice(cursor, user, move_line, type)
                account_analytic_id = self._get_account_analytic_invoice(cursor,user, picking, move_line)
                
                account_id = self.pool.get('account.fiscal.position').map_account(cursor, user, partner.property_account_position, account_id)
                # se agrego para buscar el id de la cuenta de reserva al detalle
                invoice_line_vals = {
                     'name': name,
                    'origin':origin,
                    'invoice_id': invoice_id,
                    'uos_id': move_line.product_uos.id,
                    'product_id': move_line.product_id.id,
                    'account_id': account_id,
                    'price_unit': price_unit,
                    'price_standard': price_std or 0.0,
                    'price_fact': price_fact or 0.0,
                    'discount': discount,
                    'quantity': move_line.product_qty,
                    'quantity_received': move_line.product_qty,
                    'invoice_line_tax_id': [(6, 0, tax_ids)],
                    'account_analytic_id': account_analytic_id,
                    'account_res_id': account_res_id,
                }
                ##-----------------------------------------------------------------------------------------------
                ##-----------------------------------------------------------------------------------------------
                #Modificado:  Corvus Latinoamerica
                #Obtener el ID pricelist-partnerinfo para poder                     
                supplierinfo_id =0
                sql = "SELECT id    FROM product_supplierinfo WHERE product_id = %d;"%move_line.product_id.id 
                cursor.execute (sql)
                resinfo = cursor.fetchall()
                if resinfo:    
                    supplierinfo_id = resinfo[0][0]
                    invoice_line_vals['suppinfo_id'] = supplierinfo_id
                ##------------------------------------------------------------------------------------------------
                invoice_line_id = invoice_line_obj.create(cursor, user, invoice_line_vals, context=context)
                self._invoice_line_hook(cursor, user, move_line, invoice_line_id)
            invoice_obj.button_compute(cursor, user, [invoice_id], context=context, set_total=(type in ('in_invoice', 'in_refund')))
            self.write(cursor, user, [picking.id], { 'invoice_state': 'invoiced',   }, context=context)
            self._invoice_hook(cursor, user, picking, invoice_id)
        self.write(cursor, user, res.keys(), { 'invoice_state': 'invoiced',   }, context=context)
        if type == 'out_invoice': 
            return {}
        return res


    ##onchange_warehouse_id--------------------------------------------------------------------------------------------
    # Cambia el id de la ubicacion de origen al cambiar el warehouse de origen
    # Realizado por: Javier Duran
    # Fecha:12-06-09

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id, type1, type2, location_dest_id=None):
        loc_id = False
        if not warehouse_id:
            return {}
        if type1=='internal':
            loc_obj = self.pool.get('stock.location')
            if type2=='trans':
                w_name = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['name'])[0]['name']
                loc_name = 'Produccion ' + w_name
                loc_id = loc_obj.search(cr, uid, [('name', 'ilike', loc_name)])[0]
                if not loc_id:
                    raise osv.except_osv('ERROR    ', 'No hay ubicacion de produccion definida para este almacen')
            if type2=='mues':
                w_name = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['name'])[0]['name']
                loc_name = 'Muestreo ' + w_name
                loc_id = loc_obj.search(cr, uid, [('name', 'ilike', loc_name)])[0]
                if not loc_id:
                    raise osv.except_osv('ERROR    ', 'No hay ubicacion de muestreo definida para este almacen')
            if type2=='tras':
                loc_id = location_dest_id


        res = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['lot_input_id'])[0]['lot_input_id'][0]
        return {'value':{'location_id': res, 'location_dest_id': loc_id}}

    ##onchange_warehouse_dest_id--------------------------------------------------------------------------------------------
    # Cambia el id de la ubicacion de destino al cambiar el warehouse de destino
    # Realizado por: Javier Duran
    # Fecha:12-06-09

    def onchange_warehouse_dest_id(self, cr, uid, ids, warehouse_id, type1, type2, location_id=None):
        loc_id = False
        if not warehouse_id:
            return {}
        if type1=='internal':
            if type2=='trans':
                w_name = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['name'])[0]['name']
                loc_obj = self.pool.get('stock.location')
                loc_name = 'Produccion ' + w_name
                loc_id = loc_obj.search(cr, uid, [('name', 'ilike', loc_name)])[0]
                if not loc_id:
                    raise osv.except_osv('ERROR    ', 'No hay ubicacion de produccion definida para este almacen')
            if type2=='tras':
                loc_id = location_id
        if type1=='out':
            loc_obj = self.pool.get('stock.location')
            if type2=='aju':
                w_name = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['name'])[0]['name']
                loc_name = 'supplier'
                loc_id = loc_obj.search(cr, uid, [('usage', '=', loc_name)])[0]
                if not loc_id:
                    raise osv.except_osv('ERROR    ', 'No hay ubicacion de proveedores definida')


        res = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['lot_input_id'])[0]['lot_input_id'][0]
        return {'value':{'location_dest_id': res, 'location_id': loc_id}}

    ##onchange_warehouse_dest_id--------------------------------------------------------------------------------------------
    # Cambia el id de la ubicacion de orgigen o de destino del almacen
    # Realizado por: William
    # Fecha:2013
    def onchange_warehouse_location(self, cr, uid, ids, warehouse_id,location='ORIG'):
        loc_org_id = False
        loc_dest_id = False
        vals = {}
        if not warehouse_id:
            return {}
        res = self.pool.get('stock.warehouse').read(cr, uid, [warehouse_id], ['lot_stock_id','lot_output_id'])
        if res:
            loc_org_id  = res[0]['lot_stock_id'][0]
            loc_dest_id = res[0]['lot_output_id'][0]

        if location !='ORIG':
            vals = {'value':{'location_dest_id': loc_org_id}}
        else:
            vals = {'value':{'location_id': loc_org_id}}
        return vals

    ##action_confirm--------------------------------------------------------------------------------------------
    # Se sobreescribe este proceso para valorizar los movimientos internos
    # Realizado por: Javier Duran
    # Fecha:17-09-09

    def action_confirm(self, cr, uid, ids, context={}):
        # se agrego para valorizar el picking
        move_obj = pooler.get_pool(cr.dbname).get('stock.move')
        self.write(cr, uid, ids, {'state': 'confirmed'})
        todo = []
        for picking in self.browse(cr, uid, ids):
            for r in picking.move_lines:
                # se agrego para valorizar el picking
                #move_obj.write(cr, uid, [r.id], {'price_unit': r.product_id.cost_price})
                move_obj.write(cr, uid, [r.id], {'price_unit': r.product_id.standard_price})
                if r.state=='draft':
                    todo.append(r.id)
        todo = self.action_explode(cr, uid, todo, context)
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo, context)
        return True

    ##action_cancel--------------------------------------------------------------------------------------------
    # Se sobreescribe este proceso para asignar la fecha en que se cancela la nota de salida 
    # Realizado por: William S.
    # Fecha:01-12-09

    def action_cancel(self, cr, uid, ids, context={}):
        for pick in self.browse(cr, uid, ids):
            ids2 = [move.id for move in pick.move_lines]
            self.pool.get('stock.move').action_cancel(cr, uid, ids2, context)
        self.write(cr,uid, ids, {'state':'cancel', 'invoice_state':'none','date_cancel': time.strftime('%Y-%m-%d')})
        return True
        
stock_picking()



#----------------------------------------------------------
# Stock Move
#----------------------------------------------------------
class stock_move(osv.osv):
    _inherit = "stock.move"


    ##action_done--------------------------------------------------------------------------------------------
    # Se sobreescribe este proceso para valorizar los movimientos internos
    # Realizado por: Javier Duran
    # Fecha:14-09-09

    def action_done(self, cr, uid, ids, context=None):
        track_flag=False
        for move in self.browse(cr, uid, ids):
            if move.move_dest_id.id and (move.state != 'done'):
                mid = move.move_dest_id.id
                cr.execute('insert into stock_move_history_ids (parent_id,child_id) values (%s,%s)', (move.id, move.move_dest_id.id))
                if move.move_dest_id.state in ('waiting','confirmed'):
                    self.write(cr, uid, [move.move_dest_id.id], {'state':'assigned'})
                    if move.move_dest_id.picking_id:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_write(uid, 'stock.picking', move.move_dest_id.picking_id.id, cr)
                    else:
                        pass
                        # self.action_done(cr, uid, [move.move_dest_id.id])
                    if move.move_dest_id.auto_validate:
                        self.action_done(cr, uid, [move.move_dest_id.id], context=context)

            #
            # Accounting Entries
            #
            acc_src = None
            acc_dest = None
            if move.location_id.account_id:
                acc_src =  move.location_id.account_id.id
            if move.location_dest_id.account_id:
                acc_dest =  move.location_dest_id.account_id.id
            if acc_src or acc_dest:
                test = [('product.product', move.product_id.id)]
                if move.product_id.categ_id:
                    test.append( ('product.category', move.product_id.categ_id.id) )
                if not acc_src:
                    acc_src = move.product_id.product_tmpl_id.\
                            property_stock_account_input.id
                    if not acc_src:
                        acc_src = move.product_id.categ_id.\
                                property_stock_account_input_categ.id
                    if not acc_src:
                        raise osv.except_osv(_('Error!'),
                                _('There is no stock input account defined ' \
                                        'for this product: "%s" (id: %d)') % \
                                        (move.product_id.name,
                                            move.product_id.id,))
                if not acc_dest:
                    acc_dest = move.product_id.product_tmpl_id.\
                            property_stock_account_output.id
                    if not acc_dest:
                        acc_dest = move.product_id.categ_id.\
                                property_stock_account_output_categ.id
                    if not acc_dest:
                        raise osv.except_osv(_('Error!'),
                                _('There is no stock output account defined ' \
                                        'for this product: "%s" (id: %d)') % \
                                        (move.product_id.name,
                                            move.product_id.id,))
                if not move.product_id.categ_id.property_stock_journal.id:
                    raise osv.except_osv(_('Error!'),
                        _('There is no journal defined '\
                            'on the product category: "%s" (id: %d)') % \
                            (move.product_id.categ_id.name,
                                move.product_id.categ_id.id,))
                journal_id = move.product_id.categ_id.property_stock_journal.id
                if acc_src != acc_dest:
                    ref = move.picking_id and move.picking_id.name or False

                    if move.product_id.cost_method == 'average' and move.price_unit:
                        amount = move.product_qty * move.price_unit
                    else:
                        amount = move.product_qty * move.product_id.standard_price

                    # se agrego el campo pick_val para valorizar el picking
                    if move.product_id.pick_val:
                        if move.price_unit:
                            amount = move.product_qty * move.price_unit
                        else:
                            raise osv.except_osv('ERROR    ', 'Hay Producto(s) sin Valorizar')
                    # ----------------------------------------------------------------------------
                    date = time.strftime('%Y-%m-%d')
                    partner_id = False
                    if move.picking_id:
                        partner_id = move.picking_id.address_id and (move.picking_id.address_id.partner_id and move.picking_id.address_id.partner_id.id or False) or False
                    lines = [
                            (0, 0, {
                                'name': move.name,
                                'quantity': move.product_qty,
                                'credit': amount,
                                'account_id': acc_src,
                                'ref': ref,
                                'date': date,
                                'partner_id': partner_id}),
                            (0, 0, {
                                'name': move.name,
                                'quantity': move.product_qty,
                                'debit': amount,
                                'account_id': acc_dest,
                                'ref': ref,
                                'date': date,
                                'partner_id': partner_id})
                    ]
                    self.pool.get('account.move').create(cr, uid, {
                        'name': move.name,
                        'journal_id': journal_id,
                        'line_id': lines,
                        'ref': ref,
                    })
        self.write(cr, uid, ids, {'state':'done','date_planned':time.strftime('%Y-%m-%d %H:%M:%S')})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_trigger(uid, 'stock.move', id, cr)
        return True


stock_move()

#----------------------------------------------------------
# Pstock.inventory
#----------------------------------------------------------
class stock_inventory(osv.osv):
    _inherit = "stock.inventory"
    _columns = {
                'period_id': fields.many2one('period.generalperiod','Period'),
                'warehouse_id': fields.many2one('stock.warehouse','Warehouse'), 
                'confirmed': fields.boolean('Confirmado'),
                'inventory_start': fields.boolean('Apertura'),
    }
    _defaults = {
                'confirmed': lambda *a: 0,
                'inventory_start': lambda *a: 0,
    }

    def button_set_products_open(self, cr, uid, ids, context={}):
        vals = {}
        product_id = 0
        uom = 0
        if not ids:
            return vals
        obj_stock = self.pool.get('stock.inventory')
        stock = obj_stock.browse(cr, uid, ids[0])
        if not stock:
            return vals
        if not stock.warehouse_id:
            raise osv.except_osv(_('Alerta :'),_('Debe indicar el Almacen'))
        if not stock.period_id:
            raise osv.except_osv(_('Alerta :'),_('Debe indicar el Periodo'))
        if stock.inventory_line_id:
            raise osv.except_osv(_('Alerta :'),_('Ya hay Productos cargados!!!') )
        loc_id = stock.warehouse_id.lot_stock_id.id
        warehouse_id = stock.warehouse_id.id
        sql = """ 
        SELECT pp.id,pt.uom_id 
        FROM product_product                 AS pp 
        INNER JOIN product_template          AS pt ON pp.product_tmpl_id = pt.id 
        WHERE pp.active=True 
        ORDER BY pp.default_code
        """
        cr.execute(sql)
        list = cr.fetchall()
        for p in list:
            product_id = p[0]
            uom  = p[1]
            cost = 0
            list_price = 0
            standard_price = 0
            public_price = 0 
            prod  = self.pool.get('product.product').read(cr, uid, [ product_id ], ['cost_price','uom_id','list_price','standard_price','publ_price'])
            if prod and prod[0]:
                cost = prod[0]['cost_price']
                list_price = prod[0]['list_price']
                standard_price = prod[0]['standard_price']
                public_price = prod[0]['publ_price']
            vals = {
                'inventory_line_id':[(0,0,{
                                            'location_id': loc_id,
                                            'product_uom': uom,
                                            'cost_standard':cost,
                                            'public_price':public_price,
                                            'list_price': list_price,
                                            'standard_price': standard_price,
                                            'product_qty':0,
                                            'product_id': product_id,
                                            })]
            }
            self.write(cr, uid, ids, vals)
        return True

    def button_set_products(self, cr, uid, ids, context={}):
        #Inicializacion Variables
        vals = {}
        loc_id = 0
        shop_id = 0
        fdesde = ''
        fhasta = ''
        product_id = 0
        uom = 0
        qty = 0
        cost = 0
        obj_stock = self.pool.get('stock.inventory')
        stock = obj_stock.browse(cr, uid, ids[0])    
        if not ids:
            return vals
        if not stock:
            return vals
        if not stock.warehouse_id:
            raise osv.except_osv(_('Alerta :'),_('Debe indicar el Almacen'))
        if not stock.period_id:
            raise osv.except_osv(_('Alerta :'),_('Debe indicar el Periodo'))
        if stock.inventory_line_id:
            raise osv.except_osv(_('Alerta :'),_('Ya hay Productos cargados!!!') )
        loc_id = stock.warehouse_id.lot_stock_id.id
        warehouse_id = stock.warehouse_id.id
        shop_id = self.pool.get('sale.shop').search(cr, uid,[('warehouse_id','=',warehouse_id)])
        if shop_id:
            if len(shop_id) > 1:
                shop_id = tuple(str(shop_id))
            else:
                shop_id = '('+str(shop_id[0])+')'
        else:
            shop_id = 0
        #shop_id = tuple(map(lambda x: str(x),shop_id))
        fdesde = stock.period_id.date_start
        fhasta = stock.period_id.date_stop
        fdy    = fdesde[:4]
        fdm    = fdesde[5:7]
        fdd    = fdesde[8:10]
        fechaant  = '' 
        if ((int(fdm) == 1) and (int(fdd)==1)):
            fdm='12'
            fdd='31'
            fdy=str(int(fdy)-1)
            fechaant=fdy+'-'+fdm+'-'+fdd
        elif int(fdd) == 1:
            if (int(fdm)==05) or (int(fdm)==07) or (int(fdm)==10) or (int(fdm)==12):
                fdm=str(int(fdm)-1)
                fdd='30'
            elif (int(fdm)==03) :
                if int(fdy) % 4 == 0 and int(fdy) % 100 != 0 or int(fdy) % 400 == 0:
                    fdm=str(int(fdm)-1)
                    fdd='29'
                else:
                    fdm=str(int(fdm)-1)
                    fdd='28'
            else:
                fdm=str(int(fdm)-1)
                fdd='31'
            if len(fdm)==1:
                fdm='0'+fdm
            if len(fdd)==1:
                fdd='0'+fdd
            fechaant=fdy+'-'+fdm+'-'+fdd
        else:
            fdd=str(int(fdd)-1)
            if len(fdd)==1:
                fdd='0'+fdd
            if len(fdm)==1:
                fdm='0'+fdm
            fechaant=fdy+'-'+fdm+'-'+fdd
        before_period_id = self.pool.get('period.generalperiod').search(cr,uid,[('date_stop','=',fechaant) ]) 
        #fdesde[:-1]+str(int(fdesde[-1])-1))
        #'31-12-2009' 

        sql = """SELECT  
        pt.standard_price,
        pp.id ,
        COALESCE(compr.cr,0) AS comprecibida, 
        COALESCE(comprPast.cr,0) AS comprecibidaPast,
        COALESCE(compp.cp,0)+COALESCE(compDoneAfter.cda,0)+COALESCE(compCancelAfter.cca,0) AS compproceso,
        COALESCE(compCancelPast.cc,0) AS compcancelpast,
        COALESCE(compCancel.cc,0) AS compCancel,
        COALESCE(ventas.vent,0) AS ventas,
        COALESCE(ventasDonePast.vent,0) AS ventasDonePast,
        COALESCE(ventasAssigned.vent,0)+COALESCE(ventCancelAfter.vca,0)+COALESCE(ventDoneAfter.vda,0) AS ventasAssigned,
        COALESCE(ventasCancelPast.vent,0) AS ventascancelpast,
        COALESCE(ventasCancel.vent,0) AS ventasCancel,
        COALESCE(trasin.ti,0) AS trasin,
        COALESCE(trasout.to,0) AS trasout,
        COALESCE(ajuin.ai,0) AS ajuin,
        COALESCE(ajuout.ao,0) AS ajuout,
        COALESCE(nota.nt,0) AS notacredito,
        COALESCE(mues.mu,0) AS mues,
        COALESCE(compr.cr,0)+COALESCE(comprPast.cr,0)+COALESCE(nota.nt,0)+COALESCE(ajuin.ai,0)+COALESCE(trasin.ti,0)+COALESCE(transtransin.ti,0)+COALESCE(last_total.lt,0) 
        - COALESCE(mues.mu,0)-COALESCE(ajuout.ao,0)-COALESCE(trasout.to,0)-COALESCE(transtransout.to,0)-(COALESCE(ventas.vent,0)+(COALESCE(ventasAssigned.vent,0))
        -COALESCE(ventasCancelPast.vent,0))AS total,
        COALESCE(compr.cr,0)+COALESCE(comprPast.cr,0)+COALESCE(nota.nt,0)+COALESCE(ajuin.ai,0)+COALESCE(trasin.ti,0)+COALESCE(transtransin.ti,0)+COALESCE(last_total_real.lt,0)
        - COALESCE(mues.mu,0)-COALESCE(ajuout.ao,0)-COALESCE(trasout.to,0)-COALESCE(transtransout.to,0)-(COALESCE(ventas.vent,0)+COALESCE(ventasDonePast.vent,0)) 
        AS total_real,
        COALESCE(purchase_order.po,0) AS po,
        COALESCE(sale_order.so,0),
        COALESCE(transtransin.ti,0) AS transtransin,
        COALESCE(transtransout.to,0) AS transtransout,
        COALESCE(last_total.lt,0) AS last_total,
        COALESCE(last_total_real.lt,0) AS last_total_real 
        FROM product_product AS pp  
        INNER JOIN product_template AS pt ON pp.product_tmpl_id = pt.id   
        LEFT JOIN product_supplierinfo as ps ON pp.id = ps.product_id  
        LEFT JOIN (
            SELECT sum(sm.product_qty) AS cr,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND  sp.type = 'in' AND sp.type2 ='def' 
            AND sp.warehouse_id = %(w_id)s AND sp.date::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s'
            GROUP BY pp.id
            ) AS compr ON pp.id = compr.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS cp,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'assigned' AND  sp.type = 'in' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS compp ON pp.id = compp.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS cda,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state IN ('done') AND  sp.type = 'in' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date_done::date > '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS compDoneAfter ON pp.id = compDoneAfter.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS cca,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state IN ('cancel') AND  sp.type = 'in' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date_cancel::date > '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS compCancelAfter ON pp.id = compCancelAfter.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS cc,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state IN ('cancel') AND  sp.type = 'in' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_cancel::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date::date >= '%(fdesde)s' 
            GROUP BY pp.id 
            ) AS compCancel ON pp.id = compCancel.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS cc,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state IN ('cancel') AND  sp.type = 'in' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_cancel::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date::date <'%(fdesde)s' 
            GROUP BY pp.id 
            ) AS compCancelPast ON pp.id = compCancelPast.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS cr,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.type = 'in' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date::date < '%(fdesde)s' 
            GROUP BY pp.id 
            ) AS comprPast ON pp.id = comprPast.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS ai,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND  sp.type = 'in' AND sp.type2 ='aju' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ajuin ON pp.id = ajuin.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS ao,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND  sp.type = 'out' AND sp.type2 ='aju' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ajuout ON pp.id = ajuout.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as vent ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.state IN ('done') AND sm.state IN ('done') AND sp.type = 'out' AND sp.type2 ='def' 
            AND sp.warehouse_id = %(w_id)s AND so.date_order::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ventas ON pp.id = ventas.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS vca,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.state IN ('cancel') AND  sp.type = 'out' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND so.date_order::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date_cancel::date > '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ventCancelAfter ON pp.id = ventCancelAfter.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) AS vda,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.state IN ('done') AND  sp.type = 'out' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND so.date_order::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND sp.date_done::date > '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ventDoneAfter ON pp.id = ventDoneAfter.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as vent ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.state IN ('assigned') AND sm.state IN ('assigned') AND sp.type = 'out' AND sp.type2 ='def' 
            AND sp.warehouse_id = %(w_id)s AND so.date_order::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ventasAssigned ON pp.id = ventasAssigned.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as vent ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.state IN ('cancel') AND sm.state IN ('cancel') AND sp.type = 'out' AND sp.type2 ='def' 
            AND sp.warehouse_id = %(w_id)s AND so.date_order::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            AND sp.date_cancel::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS ventasCancel ON pp.id = ventasCancel.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as vent ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.type = 'out' AND sp.type2 ='def' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND so.date_order::date < '%(fdesde)s' 
            GROUP BY pp.id 
            ) AS ventasDonePast ON pp.id = ventasDonePast.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as vent ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            INNER JOIN sale_order AS so ON so.id = sp.sale_id 
            WHERE sp.state IN ('cancel') AND sm.state IN ('cancel') AND sp.type = 'out' AND sp.type2 ='def' 
            AND sp.warehouse_id = %(w_id)s AND sp.date_cancel::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            AND so.date_order::date < '%(fdesde)s' 
            GROUP BY pp.id 
            ) AS ventasCancelPast ON pp.id = ventasCancelPast.product_id 
        FULL OUTER JOIN (
            SELECT COALESCE(SUM(COALESCE(l.quantity,0)),0) as nt,l.product_id AS product_id 
            FROM   account_invoice              AS a 
            INNER JOIN account_invoice_line     AS l ON a.id=l.invoice_id 
            WHERE  a.internal=False AND a.adjustment=False AND a.type='out_refund' AND a.state!='cancel' 
            AND a.date_invoice BETWEEN '%(fdesde)s' AND '%(fhasta)s' AND a.warehouse_id = %(w_id)s 
            GROUP BY l.product_id 
            ) AS nota ON pp.id = nota.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as mu ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND sp.type = 'internal' AND sp.type2 ='mues' AND sp.warehouse_id = %(w_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS mues ON pp.id = mues.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as to ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND sp.type = 'internal' AND sp.type2 ='tras' 
            AND sm.location_id = %(loc_id)s AND sm.location_dest_id != %(loc_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS trasout ON pp.id = trasout.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as ti ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND sp.type = 'internal' AND sp.type2 ='tras' 
            AND sm.location_id != %(loc_id)s AND sm.location_dest_id = %(loc_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS trasin ON pp.id = trasin.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as to ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND sp.type = 'internal' AND sp.type2 ='trans' 
            AND sm.location_id = %(loc_id)s AND sm.location_dest_id != %(loc_id)s 
            AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            GROUP BY pp.id 
            ) AS transtransout ON pp.id = transtransout.product_id 
        FULL OUTER JOIN (
            SELECT sum(sm.product_qty) as ti ,pp.id AS product_id 
            FROM stock_picking AS sp 
            INNER JOIN stock_move AS sm ON sm.picking_id = sp.id 
            INNER JOIN product_product AS pp ON sm.product_id = pp.id 
            WHERE sp.state = 'done' AND sp.type = 'internal' AND sp.type2 ='trans' AND sm.location_id != %(loc_id)s 
            AND sm.location_dest_id = %(loc_id)s AND sp.date_done::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            group by pp.id 
            ) AS transtransin ON pp.id = transtransin.product_id 
        FULL OUTER JOIN (
            SELECT sum(pol.product_qty) as po ,pp.id AS product_id 
            FROM purchase_order AS po 
            INNER JOIN purchase_order_line AS pol ON pol.order_id = po.id 
            INNER JOIN product_product AS pp ON pol.product_id = pp.id 
            WHERE po.state IN ('done','progress') AND po.location_id = %(loc_id)s 
            AND po.date_approve::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            group by pp.id 
            ) AS purchase_order ON pp.id = purchase_order.product_id 
        FULL OUTER JOIN (
            SELECT sum(sol.product_uom_qty) as so ,pp.id AS product_id 
            FROM sale_order AS so 
            INNER JOIN sale_order_line AS sol ON sol.order_id = so.id 
            INNER JOIN product_product AS pp ON sol.product_id = pp.id 
            WHERE so.state IN ('done','progress') AND so.shop_id IN %(shop_id)s 
            AND so.date_order::date BETWEEN '%(fdesde)s' AND '%(fhasta)s' 
            group by pp.id 
            ) AS sale_order ON pp.id = sale_order.product_id 
        FULL OUTER JOIN (
            SELECT sum(sil.total_qty) as lt ,pp.id AS product_id 
            FROM stock_inventory AS si 
            INNER JOIN stock_inventory_line AS sil on sil.inventory_id = si.id 
            INNER JOIN product_product AS pp ON sil.product_id = pp.id 
            WHERE si.period_id = '%(bp_id)s' AND si.warehouse_id = '%(w_id)s' 
            group by pp.id 
            ) AS last_total ON pp.id = last_total.product_id 
        FULL OUTER JOIN (
            SELECT sum(sil.total_real_qty) as lt ,pp.id AS product_id FROM stock_inventory AS si 
            INNER JOIN stock_inventory_line AS sil on sil.inventory_id = si.id 
            INNER JOIN product_product AS pp ON sil.product_id = pp.id 
            WHERE si.period_id = '%(bp_id)s' AND si.warehouse_id = '%(w_id)s' 
            group by pp.id 
            ) AS last_total_real ON pp.id = last_total_real.product_id 
        WHERE pp.active = True 
        ORDER BY ps.name,pp.default_code
        """%{'w_id':warehouse_id,'fdesde':fdesde,'fhasta':fhasta,'loc_id':loc_id,'shop_id': shop_id,'bp_id':before_period_id[0]}
        cr.execute(sql)
        list = cr.fetchall()
        for p in list:
            cost = 0
            uom  = 0
            prod  = self.pool.get('product.product').read(cr, uid, [ p[1] ], ['cost_price','uom_id','list_price','standard_price','publ_price'])
            if prod and prod[0]:
                cost = prod[0]['cost_price']
                uom  = prod[0]['uom_id'][0]
                list_price = prod[0]['list_price']
                standard_price = prod[0]['standard_price']
                public_price = prod[0]['publ_price']
            #print public_price,cost,standard_price,list_price
            vals = {
                    'inventory_line_id':[(0,0,{
                                                'location_id': loc_id,
                                                'product_uom': uom,
                                                'cost_standard':cost,
                                                'public_price':public_price,
                                                'list_price': list_price,
                                                'standard_price': standard_price, 
                                                'product_qty':p[19],   #Fisico = Total Real - qty
                                                'product_id': p[1],
                                                'purchase_done_qty':p[2],
                                                'purchase_done_past_qty':p[3],
                                                'purchase_assig_qty':p[4],
                                                'purchase_cancel_past_qty':p[5],#Cancelados de assigned fuera del periodo que 
                                                                                #se cancelaron en este periodo
                                                'purchase_cancel_qty':p[6],
                                                'sale_done_qty':p[7],
                                                'sale_done_past_qty':p[8],
                                                'sale_assig_qty':p[9],
                                                'sale_cancel_past_qty':p[10],
                                                'sale_cancel_qty':p[11],
                                                'tars_in_qty':p[12],
                                                'tars_out_qty':p[13],
                                                'adjust_in_qty':p[14],
                                                'adjust_out_qty':p[15],
                                                'refund_qty':p[16],
                                                'muest_qty':p[17],
                                                'total_qty': p[18],
                                                'total_real_qty': p[19],
                                                'notas_purchase_qty':p[20], 
                                                'notas_sale_qty':p[21],
                                                'trans_in_qty':p[22],
                                                'trans_out_qty':p[23],
                                                'total_past_qty':p[24],
                                                'total_real_past_qty':p[25],
                                                })]
            }
            self.write(cr, uid, ids, vals)   
            #break
        return True

    def button_set_totales(self, cr, uid, ids, context={}):
        obj_stock = self.pool.get('stock.inventory')
        stock = obj_stock.browse(cr, uid, ids[0])
        fd          = stock.period_id.date_start
        fh          = stock.period_id.date_stop
        almacen_id  = stock.warehouse_id.id
        loc_id      = stock.warehouse_id.lot_stock_id.id
        #Archivo Actualizacion-----------------------------------------------------------------------------------------
        ruta	  = "/home/public/" # Ruta Desarrollo
        filename  = ruta+stock.name+'.csv'
        output    = open(filename,"w")
        output.write("Codigo;vrealizadas;vrealizadas ant;vpendientes;vcancelada ant;vcancelada;tarspaso E; traspaso S; transf E;trans S; NC; Total;TotalPED;0 \t\n")  
        cnt = 0
        for prod in stock.inventory_line_id:
            #print prod.product_id.id
            #Inicializacion Variables---------------------------------------------------------------------------------
            v_done      = 0
            v_doneant   = 0
            v_cancel    = 0
            v_cancelant = 0
            v_assig     = 0
            v_assigp    = 0
            trans_in    = 0
            trans_out   = 0
            trasp_in    = 0
            trasp_out   = 0
            ajust_in    = 0
            ajust_out   = 0
            muestreo    = 0
            notas_cre   = 0
            ttcomp      = 0
            ttvent      = 0
            ttotros     = 0
            total       = 0
            prod_id     = prod.product_id.id
            line_id     = prod.id
            #Ventas Canceladas Ant------------------------------------------------------------------------------------------
            sql_cancelant="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM       sale_order                AS o 
            INNER JOIN stock_picking             AS s ON o.id=s.sale_id 
            INNER JOIN stock_move                AS m ON s.id=m.picking_id 
            WHERE s.warehouse_id = %d AND m.product_id = %d AND s.type = 'out' AND s.type2='def' AND s.state = 'cancel' 
            AND   o.date_order < '%s' 
            AND   s.date_cancel::date BETWEEN '%s' AND '%s';""" %(almacen_id,prod_id,fd,fd,fh) 
            cr.execute (sql_cancelant)
            rcancelant = cr.fetchall()
            if rcancelant and rcancelant[0] and rcancelant[0][0]:
                v_cancelant = rcancelant[0][0] 
            #Ventas Canceladas ----------------------------------------------------------------------------------------
            sql_cancel="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM       sale_order                AS o 
            INNER JOIN stock_picking             AS s ON o.id=s.sale_id 
            INNER JOIN stock_move                AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id = %d AND m.product_id = %d AND s.type = 'out' AND s.type2='def' AND s.state = 'cancel' 
            AND    o.date_order BETWEEN '%s' AND '%s' 
            AND s.date_cancel::date BETWEEN '%s' AND '%s';""" %(almacen_id,prod_id,fd,fh,fd,fh) 
            cr.execute (sql_cancel)
            rcancel = cr.fetchall()
            if rcancel and rcancel[0] and rcancel[0][0]:
                v_cancel = rcancel[0][0]
            #Ventas Realizadas------------------------------------------------------------------------------------------
            sql_done="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM       sale_order                AS o 
            INNER JOIN stock_picking             AS s ON o.id=s.sale_id 
            INNER JOIN stock_move                AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id = %d AND m.product_id = %d AND s.type = 'out' AND s.type2='def' AND s.state = 'done'  
            AND    o.date_order BETWEEN '%s' AND '%s' 
            AND s.date_done::date BETWEEN '%s' AND '%s';""" %(almacen_id,prod_id,fd,fh,fd,fh) 
            cr.execute (sql_done)
            rdone = cr.fetchall()
            if rdone and rdone[0] and rdone[0][0]:
                v_done = rdone[0][0]
            #Ventas Realizadas Ant--------------------------------------------------------------------------------------
            sql_doneant="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM       sale_order                AS o 
            INNER JOIN stock_picking             AS s ON o.id=s.sale_id 
            INNER JOIN stock_move                AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id = %d AND m.product_id = %d AND s.type = 'out' AND s.type2='def' AND s.state = 'done'  
            AND    o.date_order < '%s'  
            AND s.date_done::date BETWEEN '%s' AND '%s';""" %(almacen_id,prod_id,fd,fd,fh) 
            cr.execute (sql_doneant)
            rdoneant = cr.fetchall()
            if rdoneant and rdoneant[0] and rdoneant[0][0]:
                v_doneant = rdoneant[0][0]
            #Ventas Realizadas Pendientes-------------------------------------------------------------------------------
            sql_assig="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM       sale_order                AS o 
            INNER JOIN stock_picking             AS s ON o.id=s.sale_id 
            INNER JOIN stock_move                AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id = %d AND m.product_id = %d AND s.type = 'out' AND s.type2='def' AND s.state = 'assigned'   
            AND o.date_order BETWEEN '%s' AND '%s';""" %(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_assig)
            rassig = cr.fetchall()
            if rassig and rassig[0] and rassig[0][0]:
                v_assig = rassig[0][0]
            #Ventas  Posteriores-------------------------------------------------------------------------------
            sql_assigp="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM       sale_order                AS o 
            INNER JOIN stock_picking             AS s ON o.id=s.sale_id 
            INNER JOIN stock_move                AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id = %d AND m.product_id = %d AND s.type = 'out' AND s.type2='def' AND s.state in('done','cancel')  
            AND o.date_order BETWEEN '%s' AND '%s'   
            AND (s.date_done::date >  '%s' OR s.date_cancel::date > '%s');""" %(almacen_id,prod_id,fd,fh,fh,fh) 
            cr.execute (sql_assigp)
            rassigp = cr.fetchall()
            if rassigp and rassigp[0] and rassigp[0][0]:
                v_assig += rassigp[0][0]
            #Transferencia ENTRADA--------------------------------------------------------------------------------------
            sql_trans_in="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_dest_id=%d AND m.product_id=%d AND s.type='internal' AND s.type2='trans' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_trans_in)
            transin = cr.fetchall()
            if transin and transin[0]:
                trans_in = transin[0][0]
            #Transferencia SALIDA---------------------------------------------------------------------------------------
            sql_trans_out="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id=%d AND m.product_id=%d AND s.type='internal' AND s.type2='trans' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_trans_out)
            transout = cr.fetchall()
            if transout and transout[0]:
                trans_out = transout[0][0]
            #Traspaso ENTRADA-------------------------------------------------------------------------------------------
            sql_trasp_in="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_dest_id=%d AND m.product_id=%d AND s.type='internal' AND s.type2='tras' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_trasp_in)
            traspin = cr.fetchall()
            if traspin and traspin[0]:
                trasp_in = traspin[0][0]
            #Traspaso SALIDA-------------------------------------------------------------------------------------------
            sql_trasp_out="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id=%d AND m.product_id=%d AND s.type='internal' AND s.type2='tras' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_trasp_out)
            traspout = cr.fetchall()
            if traspout and traspout[0]:
                trasp_out = traspout[0][0]
            #Ajustes ENTRADA---------------------------------------------------------------------------------------------
            sql_ajus_in="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id=%d AND m.product_id=%d AND s.type='in' AND s.type2='aju' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_ajus_in)
            ajusin = cr.fetchall()
            #ajusin = False
            #ajust_in = prod.adjust_in_qty
            if ajusin and ajusin[0] and ajusin[0][0]:
                ajust_in = ajusin[0][0]
            #Ajustes SALIDA---------------------------------------------------------------------------------------------
            sql_ajus_out="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id=%d AND m.product_id=%d AND s.type='out' AND s.type2='aju' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_ajus_out)
            ajusout = cr.fetchall()
            #ajusout = False
            #ajust_out = prod.adjust_out_qty
            if ajusout and ajusout[0] and ajusout[0][0]:
                ajust_out = ajusout[0][0]
            #Muestreos-------------------------------------------------------------------------------------------------
            sql_muestreo="""
            SELECT COALESCE(SUM(COALESCE(m.product_qty,0)),0) as cajas
            FROM   stock_picking         AS s  
            INNER JOIN stock_move        AS m ON s.id=m.picking_id 
            WHERE  s.warehouse_id=%d AND m.product_id=%d AND s.type='internal' AND s.type2='mues' AND s.state = 'done' 
            AND    s.date_done::date BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_muestreo)
            muestr = cr.fetchall()
            #muestr = False
            #muestreo = prod.muest_qty
            if muestr and muestr[0] and muestr[0][0]:
                muestreo = muestr[0][0]
            #Notas Credito---------------------------------------------------------------------------------------------
            sql_nc="""
            SELECT COALESCE(SUM(COALESCE(l.quantity,0)),0) as cajas
            FROM   account_invoice              AS a  
            INNER JOIN account_invoice_line     AS l ON a.id=l.invoice_id  
            WHERE  a.warehouse_id=%d AND l.product_id=%d AND a.internal=False AND a.adjustment=False AND a.type='out_refund' AND a.state!='cancel'    
            AND  a.date_invoice BETWEEN '%s' AND '%s';"""%(almacen_id,prod_id,fd,fh) 
            cr.execute (sql_nc)
            notasc = cr.fetchall()
            if notasc and notasc[0]:
                notas_cre = notasc[0][0]
            #Total Compras----------------------------------------------------------------------------------------------
            ttcomp  = prod.total_past_qty 
            ttcomp += prod.purchase_done_qty
            ttcomp += prod.purchase_done_past_qty
            ttcomp += ajust_in
            ttcomp += trasp_in
            ttcomp += trans_in
            ttcomp += notas_cre
            #print prod.total_past_qty," + ",prod.purchase_done_qty," + ",prod.purchase_done_past_qty," + ",prod.adjust_in_qty," + ",trasp_in," + ",trans_in ," + ",notas_cre
            #Total Ventas-----------------------------------------------------------------------------------------------
            ttvent  = v_done
            ttvent += v_assig
            ttvent -= v_cancelant
            ttpedido =  v_done+ v_assig + v_cancel
            #Otros Totales------------------------------------------------------------------------------------------
            ttotros  = muestreo
            ttotros += ajust_out
            ttotros += trasp_out
            ttotros += trans_out
            #Actualiza Totales------------------------------------------------------------------------------------------
            cnt += 1
            total = ttcomp - ttvent - ttotros
            sql_update = """UPDATE stock_inventory_line SET 
            sale_done_qty        =%d,
            sale_done_past_qty   =%d,
            sale_assig_qty       =%d,
            sale_cancel_past_qty =%d,
            sale_cancel_qty      =%d,
            tars_in_qty          =%d,
            tars_out_qty         =%d,
            trans_in_qty         =%d,
            trans_out_qty        =%d,
            refund_qty           =%d,
            notas_sale_qty       =%d,
            adjust_in_qty        =%d,
            adjust_out_qty       =%d,
            muest_qty            =%d,
            total_qty=%d  
            WHERE id=%d"""%(v_done,v_doneant,v_assig,v_cancelant,v_cancel,trasp_in,trasp_out,trans_in,trans_out,notas_cre,ttpedido,ajust_in,ajust_out,muestreo,total,line_id) 
            cr.execute (sql_update)
            totalpedido = v_done + v_assig + v_cancel
            #print cnt,":  ",prod.product_id.default_code,ttcomp, ttvent, ttotros," = ", total
            output.write(prod.product_id.default_code+';'+str(v_done)+';'+str(v_doneant)+';'+str(v_assig)+';'+str(v_cancelant)+';'+str(v_cancel)+';'+ str(trasp_in)+';'+str(trasp_out)+';'+str(trans_in)+';'+str(trans_out)+';'+str(notas_cre)+';'+str(total)+';'+str(totalpedido)+ ";0\t\n") 
            #if cnt > 10:
            #    break
        output.close()  
        return True
stock_inventory()

#----------------------------------------------------------
# stock.inventory.line
#----------------------------------------------------------
class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line" 
    _columns = {
        'cost_standard': fields.float('Costo standard', digits=(16,2)),
        'purchase_done_qty': fields.integer('Compras Realizadas' ),
        'purchase_done_past_qty': fields.integer('Compras Realizadas Pasadas' ),
        'purchase_assig_qty': fields.integer('Compras Pendientes' ),
        'purchase_cancel_past_qty': fields.integer('Compras Canceladas' ),
        'purchase_cancel_qty': fields.integer('Compras Canceladas' ),
        'sale_done_qty': fields.integer('Ventas Realizadas' ),
        'sale_done_past_qty': fields.integer('Ventas Realizadas Pasadas' ),
        'sale_assig_qty': fields.integer('Ventas Pendientes' ),
        'sale_cancel_past_qty': fields.integer('Ventas Canceladas' ),
        'sale_cancel_qty': fields.integer('Ventas Canceladas' ),
        'tars_in_qty': fields.integer('Traspasos Entrada' ),#TRASPASOS != TRANSFERENCIAS
        'tars_out_qty': fields.integer('Traspasos Salida' ),
        'trans_in_qty': fields.integer('Transferencias Entrada' ),#TRANSFERENCIAS != TRASPASOS
        'trans_out_qty': fields.integer('Transferencias Salida' ),
        'adjust_in_qty': fields.integer('Ajuste Entrada' ),
        'adjust_out_qty': fields.integer('Ajuste Salida' ),
        'muest_qty': fields.integer('Ajuste Salida' ),
        'refund_qty': fields.integer('Notas Credito' ),
        'notas_purchase_qty': fields.integer('Pedidos Compra'),
        'notas_sale_qty': fields.integer('Pedidos Venta'),
        'total_qty': fields.integer('Total' ),
        'total_past_qty': fields.integer('Total Periodo Pasado' ),
        'public_price': fields.float('Precio Publico', digits=(16,2)),
        'list_price': fields.float('Precio Lista A', digits=(16,2)),
        'standard_price': fields.float('Costo Proveedor', digits=(16,2)),
        'total_real_qty': fields.integer('Total Real' ),
        'total_real_past_qty': fields.integer('Total Real Periodo Pasado' ),

    }     

stock_inventory_line()
