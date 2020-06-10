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

from osv import fields,osv,orm
import time
import netsvc
import ir
from mx import DateTime
import pooler
import tools
from tools import config

#-------------------------------------------------------------------------------------------------------------------------
#Los Campos: 
#1.-  'invoice_method': se sobreescribe para cambiar el metodo de compra, por defecto es 'order'
#                       se cambia a 'picking', para que la factura de compra se genere desde el picking o Nota de Entrada
#2.-  'name': se sobreescribe para asignarle el nro de compra a dicho campo.
#-------------------------------------------------------------------------------------------------------------------------
class purchase_order(osv.osv):
    _inherit = "purchase.order" 
    _columns = {

    }
    _defaults = {
        'invoice_method': lambda *a: 'picking',
        'name': lambda obj, cr, uid, context: obj.pool.get('purchase.order').po_seq_get(cr, uid),
    }

    ##po_seq_get-------------------------------------------------------------------------------------------------------
    #Asigna el numero a la orden de compra, el cual puede ser temporal, ya que solo cuando se guarda
    #la orden de compra, se asigna el definitivo
    #		
    def po_seq_get(self, cr, uid):
        pgp_obj = self.pool.get('period.generalperiod')
        pgp_ids = pgp_obj.find(cr, uid, tp='purchase')
        pg = pgp_obj.browse(cr, uid, pgp_ids)[0]
        to_update = {'suffix':'/'+pg.code}
        pool_seq=self.pool.get('ir.sequence')
        cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='purchase.order' and active=True")
        res = cr.dictfetchone()
        res.update(to_update)
        if res:
            if res['number_next']:
                return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
            else: 
                return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
        return False
    #-------------------------------------------------------------------------------------------------------------------

    ##create------------------------------------------------------------------------------------------------------------
    #Este porceso se llama cada vez que se crea una nueva compra.	
    #Asigna el numero de orden de compra definitivo y aumenta el contador en la secuencia 'purchase.order' 
    #
    def create(self, cr, user, vals, context=None):
        if context:
            pgp_obj = self.pool.get('period.generalperiod')
            pgp_ids = pgp_obj.find(cr, user, tp='purchase')
            pg = pgp_obj.browse(cr, user, pgp_ids)[0]
            name=self.pool.get('ir.sequence').get(cr, user, 'purchase.order')	
            vals['name']=name+'/'+pg.code
        return super(purchase_order,self).create(cr, user, vals, context)		
    #-------------------------------------------------------------------------------------------------------------------

	##action_invoice_create-------------------------------------------------------------------------------------
	#Se agrega el campo de la cuenta de reserva y el del costo adv
	# Realizado por: Javier Duran
	#Fecha:14-07-09

    def inv_line_create(self,a,ol,ar):
		return (0, False, {
			'name': ol.name,
			'account_id': a,
			'price_unit': ol.price_unit or 0.0,
			'quantity': ol.product_qty,
			'product_id': ol.product_id.id or False,
			'uos_id': ol.product_uom.id or False,
			'invoice_line_tax_id': [(6, 0, [x.id for x in ol.taxes_id])],
			'account_analytic_id': ol.account_analytic_id.id,
			'account_res_id': ar,
			'price_standard': ol.price_standard or 0.0,
		})


	##action_invoice_create-------------------------------------------------------------------------------------
	#Se agrega el id de la cuenta de reserva
	# Realizado por: Javier Duran
	#Fecha:14-07-09

    def action_invoice_create(self, cr, uid, ids, *args):
		res = False
		journal_obj = self.pool.get('account.journal')
		for o in self.browse(cr, uid, ids):
			il = []
			for ol in o.order_line:

				if ol.product_id:
					a = ol.product_id.product_tmpl_id.property_account_expense.id
					# se agrego para buscar el id de la cuenta de reserva
					ar = o.partner_id.property_account_reserv.id
					if not a:
						a = ol.product_id.categ_id.property_account_expense_categ.id
					if not a:
						raise osv.except_osv(_('Error !'), _('There is no expense account defined for this product: "%s" (id:%d)') % (ol.product_id.name, ol.product_id.id,))
				else:
					a = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category')
				fpos = o.fiscal_position or False
				a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
				il.append(self.inv_line_create(a,ol,ar))

			a = o.partner_id.property_account_payable.id
			journal_ids = journal_obj.search(cr, uid, [('type', '=','purchase')], limit=1)
			inv = {
				'name': o.partner_ref or o.name,
				'reference': "P%dPO%d" % (o.partner_id.id, o.id),
				'account_id': a,
				'type': 'in_invoice',
				'partner_id': o.partner_id.id,
				'currency_id': o.pricelist_id.currency_id.id,
				'address_invoice_id': o.partner_address_id.id,
				'address_contact_id': o.partner_address_id.id,
				'journal_id': len(journal_ids) and journal_ids[0] or False,
				'origin': o.name,
				'invoice_line': il,
				'fiscal_position': o.partner_id.property_account_position.id
			}
			inv_id = self.pool.get('account.invoice').create(cr, uid, inv, {'type':'in_invoice'})
			self.pool.get('account.invoice').button_compute(cr, uid, [inv_id], {'type':'in_invoice'}, set_total=True)

			self.write(cr, uid, [o.id], {'invoice_id': inv_id})
			res = inv_id
		return res


	##action_picking_create-------------------------------------------------------------------------------------
	#Se agrega el id del almacen, la ubicacion de origen, la destino y el tipo2
	# Realizado por: Javier Duran
	#Fecha:29-06-09

    def action_picking_create(self,cr, uid, ids, *args):
		picking_id = False
		for order in self.browse(cr, uid, ids):
			loc_id = order.partner_id.property_stock_supplier.id
			istate = 'none'
			if order.invoice_method=='picking':
				istate = '2binvoiced'
			picking_id = self.pool.get('stock.picking').create(cr, uid, {
				'origin': order.name+((order.origin and (':'+order.origin)) or ''),
				'type': 'in',
				'address_id': order.dest_address_id.id or order.partner_address_id.id,
				'invoice_state': istate,
				'purchase_id': order.id,
				'warehouse_id':order.warehouse_id.id,
				'location_id': loc_id,
				'location_dest_id': order.location_id.id,
				'type2': 'def',
			})
			for order_line in order.order_line:
				if not order_line.product_id:
					continue
				if order_line.product_id.product_tmpl_id.type in ('product', 'consu'):
					dest = order.location_id.id
					self.pool.get('stock.move').create(cr, uid, {
						'name': 'PO:'+order_line.name,
						'product_id': order_line.product_id.id,
						'product_qty': order_line.product_qty,
						'product_uos_qty': order_line.product_qty,
						'product_uom': order_line.product_uom.id,
						'product_uos': order_line.product_uom.id,
						'date_planned': order_line.date_planned,
						'location_id': loc_id,
						'location_dest_id': dest,
						'picking_id': picking_id,
						'move_dest_id': order_line.move_dest_id.id,
						'state': 'assigned',
						'purchase_line_id': order_line.id,
					})
					if order_line.move_dest_id:
						self.pool.get('stock.move').write(cr, uid, [order_line.move_dest_id.id], {'location_id':order.location_id.id})
			wf_service = netsvc.LocalService("workflow")
			wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
		return picking_id    
purchase_order()

class purchase_order_line(osv.osv):
    _inherit = "purchase.order.line" 
    _columns = {
        'price_standard': fields.float('Standard Price', digits=(16, int(config['price_accuracy']))),
    }
    _defaults = {
        'price_standard':		lambda *a: 0,
    }

    ##product_id_change------------------------------------------------------------------------------------------------------------
    #Se sobreescribe la calse para modificar la forma en la que se contruye el nombre del producto que se asigna a la orden de compra
    #
    #Originalmente es: prod_name = prod.partner_ref
    #Cambia a:  nbprod      = self.pool.get('product.product').name_get(cr,uid,[product],context)[0][1]
    #           prod_name   = nbprod
    #
    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False, fiscal_position=False):
        if not pricelist:
            raise osv.except_osv(_('No Pricelist !'), _('You have to select a pricelist in the purchase form !\nPlease set one before choosing a product.'))
        if not  partner_id:
            raise osv.except_osv(_('No Partner!'), _('You have to select a partner in the purchase form !\nPlease set one partner before choosing a product.'))
        if not product:
            return {'value': {'price_unit': 0.0, 'name':'','notes':'', 'product_uom' : False}, 'domain':{'product_uom':[]}}
        prod= self.pool.get('product.product').browse(cr, uid,product)
        lang=False
        #if partner_id:
        #    lang=self.pool.get('res.partner').read(cr, uid, partner_id)['lang']
        context={'lang':lang}
        context['partner_id'] = partner_id
        prod_uom_po = prod.uom_po_id.id
        if not uom:
            uom = prod_uom_po
        if not date_order:
            date_order = time.strftime('%Y-%m-%d')
        price = self.pool.get('product.pricelist').price_get(cr,uid,[pricelist],
                product, qty or 1.0, partner_id, {
                    'uom': uom,
                    'date': date_order,
                    })[pricelist]
        qty = 1
        seller_delay = 1
        #for s in prod.seller_ids:
        #    seller_delay = s.delay
        #    if s.name.id == partner_id:
        #        seller_delay = s.delay
        #        qty = s.qty
        dt = time.strftime('%Y-%m-%d %H:%M:%S')  #(DateTime.now() + DateTime.RelativeDateTime(days=seller_delay or 0.0)).strftime('%Y-%m-%d %H:%M:%S')
        #------------------------------------------------------------------------------------------------------------------
        #Modificado:  Corvus Latinoamerica
        #Se comenta la linea y se cambia por las dos lineas siguientes
        #prod_name = prod.partner_ref
        nbprod = self.pool.get('product.product').name_get(cr,uid,[product],context)[0][1]
        prod_name = nbprod
        #------------------------------------------------------------------------------------------------------------------
	# se agrego para buscar el costo adv del producto que sera usado en la cuenta de reserva
        #prod_pcom = prod.cost_price
        prod_pcom = prod.standard_price
		#------------------------------------------------------------------------------------------------------------------
		# se agrego para actualizar costo adv
        res = {'value': {'price_unit': price, 'name':prod_name, 'taxes_id':map(lambda x: x.id, prod.supplier_taxes_id),
            'date_planned': dt,'notes':prod.description_purchase,
            'product_qty': qty,
            'product_uom': uom,
			'price_standard': prod_pcom}}
        domain = {}
	#------------------------------------------------------------------------------------------------------------------
	#Modificado:  Corvus Latinoamerica
	#Se comentan las siguientes lineas, la posicion fiscal no se usara por lo que no se requiere procesarla
	#
        #partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
        #taxes = self.pool.get('account.tax').browse(cr, uid,map(lambda x: x.id, prod.supplier_taxes_id))
        #fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        #res['value']['taxes_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)

        res2 = self.pool.get('product.uom').read(cr, uid, [uom], ['category_id'])
        res3 = prod.uom_id.category_id.id
        domain = {'product_uom':[('category_id','=',res2[0]['category_id'][0])]}
        if res2[0]['category_id'][0] != res3:
            raise osv.except_osv(_('Wrong Product UOM !'), _('You have to select a product UOM in the same category than the purchase UOM of the product'))

        res['domain'] = domain
        return res

purchase_order_line()
