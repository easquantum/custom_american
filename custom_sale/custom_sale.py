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

import tools
import pooler
import time
import netsvc
from osv import fields, osv
import ir
from mx import DateTime
from tools import config 



class sale_order(osv.osv):
	_name = "sale.order"
	_inherit = 'sale.order'	

	_columns = {
		'nota_atencion': fields.char('Nota Atencion', size=100),
		'nota_atencion_id': fields.many2many('nota.atencion', 'sale_nota_atencion_rel', 'sale_id', 'nota_atencion_id', 'Notas Atencion'),		
		'pricelist_version_id': fields.many2one('product.pricelist.version', 'Prices list Version'),
		'code_zone_id': fields.many2one('res.partner.zone', 'Code Zone'),
		'state': fields.selection([
			('draft','Quotation'),
			('validated','Validated'),
			('waiting_date','Waiting Schedule'),
			('manual','Manual in progress'),
			('progress','In progress'),
			('shipping_except','Shipping Exception'),
			('invoice_except','Invoice Exception'),
			('done','Done'),
			('cancel','Cancel')
		], 'Order State', readonly=True, help="Gives the state of the quotation or sale order.", select=True),
		'total_qty': fields.float('Total Cajas', digits=(16, int(config['price_accuracy']))),
		
	}	
	_defaults = {
		'order_policy': lambda *a: 'picking',
		'invoice_quantity': lambda *a: 'procurement',
		'name': lambda obj, cr, uid, context: obj.pool.get('sale.order').sale_seq_get(cr, uid),
		'total_qty': lambda *a: 0
	}

	##sale_seq_get-------------------------------------------------------------------------------------------------------
	#Asigna el numero de pedido, el cual puede sera temporal, hasta que el pedido sea guardado
	#
	def sale_seq_get(self, cr, uid):
		pool_seq=self.pool.get('ir.sequence')
		cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='sale.order' and active=True")
		res = cr.dictfetchone()
		if res:
			if res['number_next']:
				return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
			else: 
				return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
		return False
	#-------------------------------------------------------------------------------------------------------------------

	##button_dummy------------------------------------------------------------------------------------------------------------	
	#Calcular total de cajas de pedido 
	#
	def button_dummy(self, cr, uid, ids, context={}):
	    if ids: 
	        order_id = ids[0]
	        sql = "SELECT SUM(product_uom_qty) as cajas FROM sale_order_line WHERE order_id=%d;"%order_id
	        cr.execute (sql)
	        result = cr.fetchall()
	        #print "SQL",sql,"RESULT",result
	        if result and result[0]:
	            vals = {'total_qty':result[0][0]}
	            self.pool.get('sale.order').write(cr, uid, ids, vals)
	    return True
	
	
	##create------------------------------------------------------------------------------------------------------------	
	#Asigna el numero de pedido definitivo y aumenta el contador en la secuencia 'sale.order' 
	#	
	def create(self, cr, user, vals, context=None):
		if context:
			pedido_nro=self.pool.get('ir.sequence').get(cr, user, 'sale.order')	
			vals['name'] = pedido_nro
			#Asignar zona
			if vals.has_key('partner_id') and  vals['partner_id']:
			    zona_id = self.pool.get('res.partner').browse(cr, user, vals['partner_id']).code_zone_id.id or False
			    if zona_id:
			        vals['code_zone_id'] = zona_id
			    else:
			        raise osv.except_osv('ERROR ', 'El cliente no tiene zona asignada. Por favor asignar zona para poder procesar el pedido!!!')
		return super(sale_order,self).create(cr, user, vals, context)		


	##write-------------------------------------------------------------------------------------------------------------------		
	def write(self, cr, uid, ids, vals, context=None):
		if ids:
			order_id = ids[0]	
			sale_obj = self.pool.get('sale.order')
			sale = sale_obj.browse(cr, uid, order_id) 
			#Asignar zona
			if vals.has_key('partner_id') and  vals['partner_id']:
			    zona_id = self.pool.get('res.partner').browse(cr, uid, vals['partner_id']).code_zone_id.id or False
			    if zona_id:
			        vals['code_zone_id'] = zona_id
			    else:
			        raise osv.except_osv('ERROR ', 'El cliente no tiene zona asignada. Por favor asignar zona para poder guarda el pedido!!!')
		return super(sale_order,self).write(cr, uid, ids, vals,context=context)		


	#onchange_partner_id:---------------------------------------------------------------------------------------------------------
	#Se sobreescribe este metodo para asignar nuevos valores automaticamente, en el momento que se selecciona el cliente
	#	
	def onchange_partner_id(self, cr, uid, ids, part):
		result	= super(sale_order, self).onchange_partner_id(cr, uid, ids, part)
		if part:
			result['value']['order_policy'] = 'picking'
			result['value']['invoice_quantity'] = 'procurement'
			#Asignar Zona:
			#Se obtiene la zona del cliente y se asigna al pedido
			zona_id = self.pool.get('res.partner').browse(cr, uid, part).code_zone_id.id or False
			result['value']['code_zone_id'] = zona_id
						
			#Asignar Almacen:
			#se consulta el cliente para obtener mediante la zona el almacen al que esta pertenece
			#luego se obtiene la tienda que corresponda con el almacen de la zona del cliente.
			if zona_id: 
				almacen	= self.pool.get('res.partner').browse(cr, uid, part).code_zone_id.warehouse_id.id
				if almacen:
					tienda_id = pooler.get_pool(cr.dbname).get('sale.shop').search(cr,uid, [('warehouse_id','=',almacen)])
					if tienda_id: 
						result['value']['shop_id'] = tienda_id[0]
			
			
			#Asignar Version lista Precios:
			#Se valida que el cliente posea una lista de precios por defecto
			#luego se obtienen las version o versiones activar para dicha lista
			#en caso de existar mas de una version activa se obtiene la que corresponde con el rango de facha actual
			if result['value'].has_key('pricelist_id'):
				priceclist_id = result['value']['pricelist_id']
				version_ids = pooler.get_pool(cr.dbname).get('product.pricelist.version').search(cr,uid, [('pricelist_id','=',priceclist_id), ('active', '=',True) ])
				if len(version_ids) > 1:
					fecha = time.strftime('%Y-%m-%d')
					version_ids = pooler.get_pool(cr.dbname).get('product.pricelist.version').search(cr,uid, [('pricelist_id','=',priceclist_id), ('active', '=',True), ('date_start','<=',fecha),('date_end','>=',fecha)])
				if version_ids:
					result['value']['pricelist_version_id'] = version_ids[0]
		return result
	#-----------------------------------------------------------------------------------------------------------------------------

	#payterm_id_change------------------------------------------------------------------------------------------------------------
	#Condiciones de Pago:
	#al cambiar la condicion de pago del pedido, se aplica a los productos del pedido el nuevo porcentaje de descuento
	#que dicha condicion de pago poseea.
	def payterm_id_change(self, cr, uid, ids,payterm_id):
		v		={}
		tax		=[]
		linep	=[]
		if ids and payterm_id:
			#Se obtienen el porcentaje de descuentos que posee la condicion de pago seleccionada
			sql = "SELECT tax_id FROM account_payment_tax_rel WHERE paymenterm_id=%d;"%payterm_id 
			cr.execute (sql)
			for inf in cr.fetchall():
				tax.append(inf[0])
			
			#Porcentajes de Descuento:
			#Se consulta si los podructos poseen algun porcentaje de descuento, de la anterior condicion de pago
			#de ser positivo, estos seran removidos 
			sqla = """
			SELECT s.id,t.tax_id,s.name 
			FROM sale_order_line AS s 
			INNER JOIN sale_order_tax AS t ON s.id=t.order_line_id 
			INNER JOIN account_payment_tax_rel AS r ON t.tax_id=r.tax_id 
			WHERE s.order_id=%d;"""%ids[0]
			cr.execute (sqla)
			for infd in cr.fetchall():
				sqld = "DELETE FROM  sale_order_tax WHERE order_line_id=%d  AND tax_id=%d;"%(infd[0],infd[1])
				cr.execute (sqld)
				linep.append(infd[0])

			#Se agrega a todos los productos el nuevo porcentaje de descuento que posea la condicion de pago seleccionada
			sqlp = """SELECT id FROM sale_order_line WHERE order_id=%d;"""%ids[0]
			cr.execute (sqlp)			
			for lp in cr.fetchall():
				for tx in tax:
					sqli = """INSERT INTO sale_order_tax (order_line_id, tax_id) VALUES(%d,%d);"""%(lp[0],tx)
					cr.execute (sqli)				
		return{'value':v}
	#--------------------------------------------------------------------------------------------------------------------------
		
	#wkf_validate_sale---------------------------------------------------------------------------------------------------------
	#Worflow que pasa de estado 'draft' a 'validate', la finalidad de este consiste en permitir al dpto. de facturacion
	#validar los pedidos y trasladarlos al dpto. de credito y cobranza.
	def wkf_validate_sale(self, cr, uid, ids):
		#Valida que el pedido no posea productos exentos y productos con impuesto, solo permite de un mismo tipo.
		contax = 0
		sintax = 0
		sqlsin ="""
		SELECT l.id 
		FROM   sale_order_line  AS l 
		WHERE l.order_id=%d 
		AND l.id NOT IN (
		SELECT st.order_line_id 
		FROM  sale_order_tax AS st 
		INNER JOIN account_tax  AS at ON st.tax_id=at.id 
		WHERE l.id = st.order_line_id AND at.tax_group='vat'
		)
		"""%ids[0]
		cr.execute (sqlsin)
		sintax = cr.fetchall()
		sqltax ="""
		SELECT      sl.id 
		FROM        sale_order_line  AS sl 
		INNER JOIN  sale_order_tax   AS st  ON sl.id=st.order_line_id 
		INNER JOIN  account_tax      AS at  ON st.tax_id=at.id 
		WHERE sl.order_id=%d AND at.tax_group='vat'
		"""%ids[0]
		cr.execute (sqltax)
		contax = cr.fetchall()
		if sintax and contax:
		    raise osv.except_osv(_('Warning !'), _('Pedido contiene productos EXENTOS y Con IVA !!!'))
		self.write(cr, uid, ids, {'state': 'validated'})
		return True		
	#--------------------------------------------------------------------------------------------------------------------------
	
	
	#action_ship_create:---------------------------------------------------------------------------------------------------------
	#Se sobreescribe este metodo para asignar nuevos valores tales como:
	#Notas Atencion: Se copian las notas de atencion que posee el pedido a la nota de salida
	#		
	def action_ship_create(self, cr, uid, ids, *args):
		picking_id=False
		company = self.pool.get('res.users').browse(cr, uid, uid).company_id
		for order in self.browse(cr, uid, ids, context={}):
			output_id = order.shop_id.warehouse_id.lot_output_id.id
			picking_id = False
			for line in order.order_line:
				proc_id=False
				date_planned = DateTime.now() + DateTime.RelativeDateTime(days=line.delay or 0.0)
				date_planned = (date_planned - DateTime.RelativeDateTime(days=company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
				if line.state == 'done':
					continue
				if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
					location_id = order.shop_id.warehouse_id.lot_stock_id.id
					if not picking_id:
						loc_dest_id = order.partner_id.property_stock_customer.id					
						vals_pk = {
							'origin': order.name,
							'type': 'out',
							'state': 'auto',
							'move_type': order.picking_policy,
							'sale_id': order.id,
							'address_id': order.partner_shipping_id.id,
							'note': order.note,
							'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
							'type2': 'def',
						}
						#------------------------------------------------------------------------------------------------
						#Modificado:  Corvus Latinoamerica
						#Fecha: 01-06-09
						#Autor: William Suarez
						#Asignar las Notas de Atencion del Pedido y el codigo de la zona
						if order.nota_atencion:
						    if order.note:
						        vals_pk['note'] += order.nota_atencion
						    else:
						        vals_pk['note'] = order.nota_atencion
						notas_ids = []
						sql = "SELECT nota_atencion_id FROM sale_nota_atencion_rel WHERE sale_id=%d;"%order.id			
						cr.execute (sql)
						for notas in cr.fetchall():
							notas_ids.append(notas[0])
						
						if notas_ids:
							vals_pk['nota_atencion_ids'] = [(6, 0, notas_ids)]
						
								
						if order.partner_id.code_zone_id:
							vals_pk['code_zone_id'] = order.partner_id.code_zone_id.id							
						if order.shop_id.warehouse_id:
							vals_pk['warehouse_id'] = order.shop_id.warehouse_id.id
						#-------------------------------------------------------------------------------------------------
						picking_id = self.pool.get('stock.picking').create(cr, uid, vals_pk)

					move_id = self.pool.get('stock.move').create(cr, uid, {
							'name': line.name[:64],
							'picking_id': picking_id,
							'product_id': line.product_id.id,
							'date_planned': date_planned,
							'product_qty': line.product_uom_qty,
							'product_uom': line.product_uom.id,
							'product_uos_qty': line.product_uos_qty,
							'product_uos': (line.product_uos and line.product_uos.id) or line.product_uom.id,
							'product_packaging' : line.product_packaging.id,
							'address_id' : line.address_allotment_id.id or order.partner_shipping_id.id,
							'location_id': location_id,
							'location_dest_id': output_id,
							'sale_line_id': line.id,
							'tracking_id': False,
							'state': 'draft',
							#'state': 'waiting',
							'note': line.notes,
					})
					proc_id = self.pool.get('mrp.procurement').create(cr, uid, {
							'name': order.name,
							'origin': order.name,
							'date_planned': date_planned,
							'product_id': line.product_id.id,
							'product_qty': line.product_uom_qty,
							'product_uom': line.product_uom.id,
							'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
							'product_uos': (line.product_uos and line.product_uos.id)      or line.product_uom.id,
							'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
							'procure_method': line.type,
							'move_id': move_id,
							'property_ids': [(6, 0, [x.id for x in line.property_ids])],
					})
					wf_service = netsvc.LocalService("workflow")
					wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
					self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
				elif line.product_id and line.product_id.product_tmpl_id.type=='service':
					proc_id = self.pool.get('mrp.procurement').create(cr, uid, {
							'name': line.name,
							'origin': order.name,
							'date_planned': date_planned,
							'product_id': line.product_id.id,
							'product_qty': line.product_uom_qty,
							'product_uom': line.product_uom.id,
							'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
							'procure_method': line.type,
							'property_ids': [(6, 0, [x.id for x in line.property_ids])],
					})
					self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
					wf_service = netsvc.LocalService("workflow")
					wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
				else:
					#
					# No procurement because no product in the sale.order.line.
					#
					pass

			val = {}
			if picking_id:
				wf_service = netsvc.LocalService("workflow")
				wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
				#--------------------------------------------------------------------------------------------------------------------
				#Modificado:  Corvus Latinoamerica
				#Fecha: 01-06-09
				#Nota: Se cambia el estatus en el picking de confirmado a asignado. Igualmente a todos sus movimentos
				self.pool.get('stock.picking').write(cr, uid, picking_id, {'state':'assigned'})
				move_ids = pooler.get_pool(cr.dbname).get('stock.move').search(cr,uid, [('picking_id','=',picking_id)]) 
				self.pool.get('stock.move').write(cr, uid, move_ids, {'state':'assigned'})
				#---------------------------------------------------------------------------------------------------------------------

			if order.state=='shipping_except':
				val['state'] = 'progress'
				if (order.order_policy == 'manual'):
					for line in order.order_line:
						if (not line.invoiced) and (line.state not in ('cancel','draft')):
							val['state'] = 'manual'
							break
			self.write(cr, uid, [order.id], val)
		return True	
	#----------------------------------------------------------------------------------------------------------------------------
	
	
	#_make_invoice:---------------------------------------------------------------------------------------------------------
	#Se sobreescribe este metodo para asignar nuevos valores tales como:
	#Notas Atencion: Se copian las notas de atencion que posee la nota de salida a la factura de venta
	#
	def _make_invoice(self, cr, uid, order, lines,context={}):
		a = order.partner_id.property_account_receivable.id
		if order.payment_term:
			pay_term = order.payment_term.id
		else:
			pay_term = False
		for preinv in order.invoice_ids:
			if preinv.state in ('open','paid','proforma'):
				for preline in preinv.invoice_line:
					inv_line_id = self.pool.get('account.invoice.line').copy(cr, uid, preline.id, {'invoice_id':False, 'price_unit':-preline.price_unit})
					lines.append(inv_line_id)
		inv = {
				'name': order.client_order_ref or order.name,
				'origin': order.name,
				'type': 'out_invoice',
				'reference': order.name,
				'account_id': a,
				'partner_id': order.partner_id.id,
				'address_invoice_id': order.partner_invoice_id.id,
				'address_contact_id': order.partner_invoice_id.id,
				'invoice_line': [(6,0,lines)],
				'currency_id' : order.pricelist_id.currency_id.id,
				'comment': order.note,
				'payment_term': pay_term,
				'fiscal_position': order.partner_id.property_account_position.id,
				'journal_id': 4, #VALOR POR DEFECTO, EN ESPERA DE LAS CTAS CONTABLES
		}
		#-----------------------------------------------------------------------------------------------------------------------------
		#Modificado:  Corvus Latinoamerica
		#Fecha: 01-06-09
		#Autor: William Suarez
		# Asignacion Nro Factura - Usando las secuencia de out 
		numero_factura = self.pool.get('ir.sequence').get(cr, uid, 'account.invoice.sales')
		inv['name'] = numero_factura

		#Asinacion de las Notas de Atencion
		sale	= pooler.get_pool(cr.dbname).get('sale.order').read(cr, uid, [order.id],['nota_atencion'])
		if sale and sale[0]:
			inv['nota_atencion'] = sale[0]['nota_atencion']
		notas_ids = []
		sql = "SELECT nota_atencion_id FROM sale_nota_atencion_rel WHERE sale_id=%d;"%order.id 			
		cr.execute (sql)
		for nota in cr.fetchall():
			notas_ids.append(nota[0])   
			if notas_ids:
				inv['nota_atencion_ids'] = [(6, 0, notas_ids)]
					
		#Asignacion del almacen
		sqla = "SELECT r.warehouse_id FROM sale_order AS s INNER JOIN sale_shop AS r  ON s.shop_id=r.id WHERE s.id=%d;"%order.id 			
		cr.execute (sqla) 
		rest = cr.fetchall()
		if rest and rest[0]:
			inv['warehouse_id'] = 	rest[0][0]
		
		#Asignacion Zona a la Factura		
		if order.code_zone_id.id:
			inv['code_zone_id'] = order.code_zone_id.id			
		#----------------------------------------------------------------------------------------------------------------------------
					
		inv_obj = self.pool.get('account.invoice')
		inv.update(self._inv_get(cr, uid, order))
		inv_id = inv_obj.create(cr, uid, inv)
		data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id],pay_term,time.strftime('%Y-%m-%d'))
		if data.get('value',False):
			inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
		inv_obj.button_compute(cr, uid, [inv_id])
		return inv_id	
	#----------------------------------------------------------------------------------------------------------------------------


sale_order()


class sale_order_line(osv.osv):
	_inherit = "sale.order.line"		
	_columns = {
		'pricelist_item_id': fields.many2one('product.pricelist.item', 'Prices list'),
		'price_standard': fields.float('Standard Price', digits=(16, int(config['price_accuracy']))),
	}
	_defaults = {
	
	}
	

	def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,uom=False, qty_uos=0, uos=False, name='', partner_id=False,lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False,payment_id=False,versionlist=False):
		if not  partner_id:
			raise osv.except_osv(_('No Customer Defined !'), _('You have to select a customer in the sale form !\nPlease set one customer before choosing a product.'))
		warning={}
		product_uom_obj = self.pool.get('product.uom')
		partner_obj = self.pool.get('res.partner')
		product_obj = self.pool.get('product.product')
		if partner_id:
			lang = partner_obj.browse(cr, uid, partner_id).lang
		context = {'lang': lang, 'partner_id': partner_id}

		if not product:
			return {'value': {'th_weight': 0,'product_packaging': False,'product_uos_qty': qty},'domain': {'product_uom': [],'product_uos': []}}

		if not date_order:
			date_order = time.strftime('%Y-%m-%d')

		result = {}
		product_obj = product_obj.browse(cr, uid, product, context=context)
		if not packaging and product_obj.packaging:
			packaging = product_obj.packaging[0].id
			result['product_packaging'] = packaging

		if packaging:
			default_uom = product_obj.uom_id and product_obj.uom_id.id
			pack = self.pool.get('product.packaging').browse(cr, uid, packaging, context)
			q = product_uom_obj._compute_qty(cr, uid, uom, pack.qty, default_uom)
			#qty = qty - qty % q + q
			if not (qty % q) == 0 :
				ean = pack.ean
				qty_pack = pack.qty
				type_ul = pack.ul
				warn_msg = "You selected a quantity of %d Units.\nBut it's not compatible with the selected packaging.\nHere is a proposition of quantities according to the packaging: " % (qty)
				warn_msg = warn_msg + "\n\nEAN: " + str(ean) + " Quantiny: " + str(qty_pack) + " Type of ul: " + str(type_ul.name)
				warning={'title':'Packing Information !','message': warn_msg }
			result['product_uom_qty'] = qty

		if uom:
			uom2 = product_uom_obj.browse(cr, uid, uom)
			if product_obj.uom_id.category_id.id <> uom2.category_id.id:
				uom = False

		if uos:
			if product_obj.uos_id:
				uos2 = product_uom_obj.browse(cr, uid, uos)
				if product_obj.uos_id.category_id.id <> uos2.category_id.id:
					uos = False
			else:
				uos = False

		result .update({'type': product_obj.procure_method})
		if product_obj.description_sale:
			result['notes'] = product_obj.description_sale
		fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
		partner = partner_obj.browse(cr, uid, partner_id)
		if update_tax: #The quantity only have changed
			result['delay'] = (product_obj.sale_delay or 0.0)
			result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)

		#Si el cliente no paga impuesto se le eliminan-------------------------------------------------------------------
		#Modificado: Corvus Latinoamerica
		if not partner.pay_taxes:
			result['tax_id'] = []
		#Asignacion de Descuentos-------------------------------------------------------------------------------------
		#Modificado: Corvus Latinoamerica
		if payment_id and result.has_key('tax_id'):
			sql = "SELECT tax_id FROM account_payment_tax_rel WHERE paymenterm_id=%d;"%payment_id
			cr.execute (sql)
			for inf in cr.fetchall():
				result['tax_id'].append(inf[0])
		#-------------------------------------------------------------------------------------------------------------
		result['name'] = product_obj.partner_ref
		domain = {}
		if (not uom) and (not uos):
			result['product_uom'] = product_obj.uom_id.id
			if product_obj.uos_id:
				result['product_uos'] = product_obj.uos_id.id
				result['product_uos_qty'] = qty * product_obj.uos_coeff
				uos_category_id = product_obj.uos_id.category_id.id
			else:
				result['product_uos'] = False
				result['product_uos_qty'] = qty
				uos_category_id = False
			result['th_weight'] = qty * product_obj.weight
			domain = {'product_uom':
						[('category_id', '=', product_obj.uom_id.category_id.id)],
						'product_uos':
						[('category_id', '=', uos_category_id)]}

		elif uos: # only happens if uom is False
			result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
			result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
			result['th_weight'] = result['product_uom_qty'] * product_obj.weight
		elif uom: # whether uos is set or not
			default_uom = product_obj.uom_id and product_obj.uom_id.id
			q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
			if product_obj.uos_id:
				result['product_uos'] = product_obj.uos_id.id
				result['product_uos_qty'] = qty * product_obj.uos_coeff
			else:
				result['product_uos'] = False
				result['product_uos_qty'] = qty
			result['th_weight'] = q * product_obj.weight        # Round the quantity up

		# get unit price
		if not pricelist:
			warning = {'title':'No Pricelist !','message':'You have to select a pricelist.'}
		else:
			price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],product, qty or 1.0, partner_id, {'uom': uom,'date': date_order,})[pricelist]
			if price is False:
				warning = {'title':'No valid pricelist line found !','message':"Couldn't find a pricelist line matching this product and quantity"}
			else:
				if versionlist: 
					sqli =  """
					SELECT  id,name  		  
					FROM 	  product_pricelist_item  
					WHERE price_version_id = %d
					ORDER BY sequence;"""%versionlist
					cr.execute (sqli)
					itemlist = cr.fetchall()
					if itemlist and itemlist[0] and itemlist[0][0]:			
						result['pricelist_item_id'] = itemlist[0][0]
				result['price_standard'] = price 
				result.update({'price_unit': price})
		return {'value': result, 'domain': domain,'warning':warning}

	
	
	def onchange_listprice(self, cr, uid, ids,product_id=False,item_id=False):	
		v={}
		#Asignar Precios Segun Lista:-------------------------------------------------------------------------------------------				
		if item_id and product_id:
			#Se obtiene el precio de venta del producto 'list_price'
			product_dat  = pooler.get_pool(cr.dbname).get('product.product').read(cr,uid, [product_id],['list_price','standard_price','publ_price','cost_price'])
			price        = product_dat[0]['list_price']
			v['price_unit']	= price
			#Se obtiene el porcentaje de descuento correspondiente a la lista seleccionada
			#se valida y se aplica el porcentaje al precio de venta del producto para obtener el nuevo precio 
			#el cual es asignado al producto del pedido
			discount  = pooler.get_pool(cr.dbname).get('product.pricelist.item').read(cr,uid, [item_id],['price_discount','base'])
			if discount[0]['price_discount'] != 0:
				idtipo = discount[0]['base']
				if idtipo > 0:
					tipos_prices  = pooler.get_pool(cr.dbname).get('product.price.type').read(cr,uid, [idtipo],['field'])
					if tipos_prices and tipos_prices[0]['field']:
						tipo = tipos_prices[0]['field']
						price = product_dat[0][tipo]
						#print "TIPO ",tipo,"PRECIO ",price,"  ", product_dat
				dscto = price *  discount[0]['price_discount']
				new_price  = price + dscto 
				v['price_unit'] = new_price 
		#--------------------------------------------------------------------------------------------------------------------		
		return {'value':v}


	def invoice_line_create(self, cr, uid, ids, context={}):
		def _get_line_qty(line):
			if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
				if line.product_uos:
					return line.product_uos_qty or 0.0
				return line.product_uom_qty
			else:
				return self.pool.get('mrp.procurement').quantity_get(cr, uid,line.procurement_id.id, context)

		def _get_line_uom(line):
			if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
				if line.product_uos:
					return line.product_uos.id
				return line.product_uom.id
			else:
				return self.pool.get('mrp.procurement').uom_get(cr, uid,line.procurement_id.id, context)

		create_ids = []
		for line in self.browse(cr, uid, ids, context):
			if not line.invoiced:
				if line.product_id:
					a =  line.product_id.product_tmpl_id.property_account_income.id
					if not a:
						a = line.product_id.categ_id.property_account_income_categ.id
					if not a:
						raise osv.except_osv(_('Error !'),
						_('There is no income account defined for this product: "%s" (id:%d)') %(line.product_id.name, line.product_id.id,))
				else:
					a = self.pool.get('ir.property').get(cr, uid,'property_account_income_categ', 'product.category',context=context)
				uosqty = _get_line_qty(line)
				uos_id = _get_line_uom(line)
				pu = 0.0
				if uosqty:
					pu = round(line.price_unit * line.product_uom_qty / uosqty,int(config['price_accuracy']))
				fpos = line.order_id.fiscal_position or False
				a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
				inv_id = self.pool.get('account.invoice.line').create(cr, uid, {
					'name': line.name,
					'origin':line.order_id.name,
					'account_id': a,
					'price_unit': pu,
					'quantity': uosqty,
					'discount': line.discount,
					'uos_id': uos_id,
					'product_id': line.product_id.id or False,
					'invoice_line_tax_id': [(6,0,[x.id for x in line.tax_id])],
					'note': line.notes,
					'account_analytic_id': line.order_id.project_id.id,
					'account_res_id': 1234,#CABLEADO 
				})
				cr.execute('insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values (%s,%s)', (line.id, inv_id))
				self.write(cr, uid, [line.id], {'invoiced':True})
				create_ids.append(inv_id)
		return create_ids
sale_order_line() 

