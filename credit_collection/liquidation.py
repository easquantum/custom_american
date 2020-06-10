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
from osv import fields,osv,orm
from tools import config
import mx.DateTime
import pooler

#delivery_guide_ruta-----------------------------------------------------------------------------------------------------------
# Esta tabla alamcena las rutas clasificada por almacen. Cada ruta debe especificar la tarifa para cada tipo de vehiculo   
#
class liquidation_shipping(osv.osv):
	_name = "liquidation.shipping"
	_description = "Liquidation Shiping" 
	_columns = {
		'name': fields.char('Liquidation Number', size=64, required=True, readonly=True),
		'carrier_company_id': fields.many2one('res.partner', 'Carrier Company',  states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)]}),
		'date_liquidation':fields.date('Date Liquidation', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)],'done':[('readonly',True)]}),
		'driver_id': fields.many2one('res.partner', 'Driver', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)]}),
		'guide_id': fields.many2one('delivery.guide', 'Guide', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)],'done':[('readonly',True)]}),
		'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)]}),
		'ruta_id': fields.many2one('guide.ruta', 'Ruta', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)]}),
		'vehiculo_id': fields.many2one('guide.vehiculo', 'Vehiculo Carga', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)]}),
		'base_amount': fields.float('Base Amount', required=True, states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)],'done':[('readonly',True)]}, digits=(16, int(config['price_accuracy']))),
		'extra_amount': fields.float('Extra Amount',  states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)],'done':[('readonly',True)]}, digits=(16, int(config['price_accuracy']))),
		'manual_amount': fields.float('Extra Amount',  digits=(16, int(config['price_accuracy'])), states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)],'cancel':[('readonly',True)],'done':[('readonly',True)]}),
		'number': fields.char('Invoice Number', size=64, states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),		
		'notes': fields.text('Notes'),
		'comment': fields.text('Comment'),
	    'comment_manual': fields.text('Comment Manual', states={'confirmed':[('readonly',True)], 'approved':[('readonly',True)]}),
		'state': fields.selection([
		    ('draft', 'Draft'),
		    ('denied','Denied'),
		    ('except', 'Except'),
		    ('confirmed', 'Confirmed'),
		    ('approved', 'Approved'),
		    ('done', 'Done'),
		    ('cancel', 'Cancelled')], 'Liquidation State', readonly=True, select=True),
		'liquidation_line': fields.one2many('liquidation.shipping.line', 'liquidation_id', 'Invoice Refund Lines'),
		'liquidation_fletes': fields.one2many('liquidation.shipping.line.fl', 'liquidation_ids', 'Fletes Lines'),
		'liquidation_esp': fields.boolean('Liquidacion Especial', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),
		'liquidation_manual': fields.boolean('Liquidacion Manual', states={'done':[('readonly',True)],'cancel':[('readonly',True)]}),		
	}
	_defaults = {
			'name': lambda obj, cr, uid, context: obj.pool.get('liquidation.shipping').liquidation_seq_get(cr, uid),
			'date_liquidation': lambda *a: time.strftime('%Y-%m-%d'),
			'state': lambda *a: 'draft',
	}

	##liquidation_seq_get-------------------------------------------------------------------------------------------------------
	#Asigna el numero de liquidacion, de forma temporal, al guardar se obtiene el definitivo
	#
	def liquidation_seq_get(self, cr, uid):
		pool_seq=self.pool.get('ir.sequence')
		cr.execute("select id,number_next,number_increment,prefix,suffix,padding from ir_sequence where code='liquidation.shipping' and active=True")
		res = cr.dictfetchone()
		if res:
			if res['number_next']:
				return pool_seq._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + pool_seq._process(res['suffix'])
			else:
				return pool_seq._process(res['prefix']) + pool_seq._process(res['suffix'])
		return False	
	


	##write---------------------------------------------------------------------------------------------------------------------
	#
	#
	def write(self, cursor, user, ids, vals, context=None):
		if vals.has_key('guide_id') and  vals['guide_id']: 
		    idguide = vals['guide_id']
		    infoguide = self.pool.get('delivery.guide').read(cursor, user, [idguide], ['carrier_company_id','driver_id','warehouse_id','ruta_id','vehiculo_id'])[0]
		    if infoguide:
		        vals['carrier_company_id']= infoguide['carrier_company_id'][0]
		        vals['driver_id']= infoguide['driver_id'][0]
		        vals['warehouse_id']= infoguide['warehouse_id'][0]
		        vals['ruta_id']= infoguide['ruta_id'][0]
		        vals['vehiculo_id']= infoguide['vehiculo_id'][0]		
		return super(liquidation_shipping, self).write(cursor, user, ids, vals,context=context)

	##create---------------------------------------------------------------------------------------------------------------------
	#Asigna el numero definitivi a la liquidacion, y aumenta el contador de la sequencia 'liquidation.shipping'
	#
	def create(self, cursor, user, vals, context=None):
		vals['name']=self.pool.get('ir.sequence').get(cursor, user, 'liquidation.shipping')
		#Las assignacion  de los datos siguientes se debe a que la vista al momento de crear una
		#liq. da fletes estan en modo solo lectura, por lo tanto debe ser llenados antes de cear la liquidacion...
		idguide = vals['guide_id']
		infoguide = self.pool.get('delivery.guide').read(cursor, user, [idguide], ['carrier_company_id','driver_id','warehouse_id','ruta_id','vehiculo_id'])[0]
		if infoguide:
		    vals['carrier_company_id']= infoguide['carrier_company_id'][0]
		    vals['driver_id']= infoguide['driver_id'][0]
		    vals['warehouse_id']= infoguide['warehouse_id'][0]
		    vals['ruta_id']= infoguide['ruta_id'][0]
		    vals['vehiculo_id']= infoguide['vehiculo_id'][0]
		lq_id=super(liquidation_shipping, self).create(cursor, user, vals,context=context)		
		return lq_id
	


	##button_compute_shipping----------------------------------------------------------------------------------------------------
	#Se Calcula el monto de la liquidacion
	#
	def button_compute_shipping(self, cr, uid, ids, context={}):
		totalflete	= 0
		dtotalflete	= 0	
		tipovh      = 0
		if not  ids:
			return {}
			
		#Datos Requiridos: se obtienen los datos necesario para realizar el calculo del Flete. 
		infoshipping = self.pool.get('liquidation.shipping').read(cr, uid, ids, ['guide_id','ruta_id','vehiculo_id'])[0]
		if infoshipping:
			guide	= infoshipping['guide_id'][0]
			ruta 	= infoshipping['ruta_id'][0]
			vh		= infoshipping['vehiculo_id'][0]
			if vh:
			    vhinfo = self.pool.get('guide.vehiculo').read(cr, uid, [vh], ['tipo_id'])[0]
			    tipovh = vhinfo['tipo_id'][0]
		else:
			return {}

		#Procesando Guia de Despacho: se obtiene los datos de la guia a procesar
		infoguide = self.pool.get('delivery.guide').read(cr, uid, [guide], ['carrier_company_id','driver_id','warehouse_id','ruta_id','vehiculo_id'])[0]
		if infoguide:	
			#Procesando Rutas - Tarifas: 
			#se obtiene los valores de las tarifas de la ruta asignadas al tipo de vehiculo					
			sqlg = """	
			SELECT  r.category_fle_id,r.price,c.name 
			FROM guide_ruta_line AS r
			INNER JOIN product_category_fle AS c ON r.category_fle_id=c.id
			WHERE r.ruta_id=%d AND r.tipo_vehiculo_id=%d ;"""%(ruta,tipovh)
			cr.execute (sqlg)		
			datos_tarifa = cr.fetchall()
			
			#Se obtienen los productos y sus catidades agrupados por categoria de fletes
			sqlp = """	
			SELECT SUM(i.quantity) as cantidad,p.id_flete 
			FROM delivery_guide_line AS l 
			INNER JOIN account_invoice_line AS i ON l.invoice_id=i.invoice_id 
			INNER JOIN product_product AS p ON i.product_id=p.id 
			WHERE l.guide_id=%d 
			GROUP BY p.id_flete ;"""%guide							
			cr.execute (sqlp)
			resultSQL = cr.fetchall()
			if not resultSQL:
				return False
			
			#Se borrar los fletes 
			fl_obj = self.pool.get('liquidation.shipping.line.fl')
			for id in ids:
				cr.execute("DELETE FROM liquidation_shipping_line_fl WHERE liquidation_ids=%s", (id,))
            	
			#Se calculo el monto neto del felte, segun se la tarifa que le corresponda lo cual depende de la categoria
			for product in resultSQL:
				costo		= 0
				total		= 0
				cantidad	= 0
				for tarf in datos_tarifa:
					if tarf[0] == product[1]:		#Se valida la categoria del flete de la tarifa con la del producto
						costo 		= tarf[1] 		#Costo de la Tarifa
						cantidad	= product[0]	#Cantidad de Productos
						total = cantidad *  costo
						totalflete += total
						#Se crea el flete en la linea de fletes					
						vals_fl = {
									'liquidation_fletes':[(0,0,{'name': tarf[2],'id_flete':tarf[0] ,'price':costo ,'quantity':cantidad})]
								}
						#fl_obj.create(cr, uid, vals_fl)
						self.pool.get('liquidation.shipping').write(cr, uid, ids, vals_fl)	
						break
						
			#Monto Reconcido: se almacena el monto neto del flete 
			if totalflete > 0:
				self.pool.get('liquidation.shipping').write(cr, uid, ids, {'base_amount': totalflete})	
						
			#Se obtienen las Notas de Credito del Flete
			dtotalflete = 0				
			sqlnc = """
			SELECT SUM(i.quantity) as cantidad,p.id_flete,a.reference,l.liquidation_esp 
			FROM liquidation_shipping_line AS l
			INNER JOIN account_invoice AS a ON l.invoice_id=a.id  
			INNER JOIN account_invoice_line AS i ON l.invoice_id=i.invoice_id 
			INNER JOIN product_product AS p ON i.product_id=p.id 
			WHERE l.liquidation_id=%d AND  a.state !='cancel'
			GROUP BY p.id_flete,a.reference,liquidation_esp ;"""%ids[0]	
			cr.execute (sqlnc)
			liq_line = cr.fetchall()
			
			#Validar si la Facturas poseen Notas de Credito
			sqlnotasc = """	
			SELECT  i.id,i.name,i.reference,i.parent_id
			FROM account_invoice AS i  
			WHERE i.type='out_refund' and i.adjustment=False and i.manual=False and  i.internal=False AND i.state !='cancel' AND i.parent_id in 
			(SELECT  i.id FROM delivery_guide_line AS l INNER JOIN account_invoice AS i ON l.invoice_id=i.id WHERE l.guide_id=%d)
			ORDER BY i.reference;"""%guide
			cr.execute (sqlnotasc)
			notas_cred = cr.fetchall()	
					
			#Se valida que las notas correspondientes a las facturas esten asignadas al flete.
			#Si existen notas y aun no estan asignadas se procede a la aignacion automatica
			#print "NC",notas_cred,"LQ";liq_line
			if not liq_line and notas_cred:
				for new in notas_cred:
					#Se obtiene nro de pedido de la factura para completar los valores a ingresar en la linea de fletes.
					invoic = self.pool.get('account.invoice').read(cr, uid, [new[3]], ['reference'])
					nro_fact = invoic[0]['reference']
					vals ={
								'liquidation_esp':True,
								'liquidation_line':[(0,0,{ 'invoice_id':new[0],'name': new[2],'sale_order':nro_fact, 'liquidation_esp':True})]
							}
					self.pool.get('liquidation.shipping').write(cr, uid, ids, vals)	
				cr.execute (sqlnc)	
				liq_line = cr.fetchall()	

			#Calculando el total neto de la notas de credito
			for inf in liq_line:
				costo = 0
				total   = 0
				if inf[3]:			
				    for tarf in datos_tarifa:
					    if tarf[0] == inf[1]:
					    	costo = tarf[1] 
					    	total = inf[0] *  costo
					    	dtotalflete += total
					    	break	
			self.pool.get('liquidation.shipping').write(cr, uid, ids, {'extra_amount': dtotalflete})		
		return True

	##button_compute_shipping----------------------------------------------------------------------------------------------------
	#Se Calcula el monto de la liquidacion
	#
	def button_compute_shipping_tras(self, cr, uid, ids, context={}):
		totalflete	= 0
		dtotalflete	= 0	
		tipovh      = 0
		if not  ids:
			return {}
		#Datos Control: se obtienen los datos de control para realizar el calculo del Flete. 
		infoshipping = self.pool.get('liquidation.shipping').read(cr, uid, ids, ['guide_id','ruta_id','vehiculo_id'])[0]
		if infoshipping:
			guide	= infoshipping['guide_id'][0]
			ruta 	= infoshipping['ruta_id'][0]
			vh		= infoshipping['vehiculo_id'][0]
			if vh:
			    vhinfo = self.pool.get('guide.vehiculo').read(cr, uid, [vh], ['tipo_id'])[0]
			    tipovh = vhinfo['tipo_id'][0]
		else:
			return {}

		#Procesando Guia de Despacho: se obtiene los datos de la guia a procesar
		infoguide = self.pool.get('delivery.guide').read(cr, uid, [guide], ['carrier_company_id','driver_id','warehouse_id','ruta_id','vehiculo_id'])[0]
		if infoguide:	
			#Procesando Rutas - Tarifas: 
			#se obtiene los valores de las tarifas de la ruta asignadas al tipo de vehiculo					
			sqlg = """	
			SELECT  r.category_fle_id,r.price,c.name 
			FROM guide_ruta_line AS r
			INNER JOIN product_category_fle AS c ON r.category_fle_id=c.id
			WHERE r.ruta_id=%d AND r.tipo_vehiculo_id=%d ;"""%(ruta,tipovh)
			cr.execute (sqlg)		
			datos_tarifa = cr.fetchall()

			#Se obtienen los productos y sus catidades agrupados por categoria de fletes
			sqlp = """	
			SELECT SUM(s.product_qty) as cantidad,p.id_flete 
			FROM delivery_guide_picking_line AS l  
			INNER JOIN stock_move AS s ON l.picking_id=s.picking_id 
			INNER JOIN product_product AS p ON s.product_id=p.id 
			WHERE l.guide_id=%d 
			GROUP BY p.id_flete ;"""%guide							
			cr.execute (sqlp)
			resultSQL = cr.fetchall()
			if not resultSQL:
				return False

			#Se borrar los fletes 
			fl_obj = self.pool.get('liquidation.shipping.line.fl')
			for id in ids:
				cr.execute("DELETE FROM liquidation_shipping_line_fl WHERE liquidation_ids=%s", (id,))

			#Se calculo el monto neto del felte, segun se la tarifa que le corresponda lo cual depende de la categoria
			for product in resultSQL:
				costo		= 0
				total		= 0
				cantidad	= 0
				for tarf in datos_tarifa:
					if tarf[0] == product[1]:		#Se valida la categoria del flete de la tarifa con la del producto
						costo 		= tarf[1] 		#Costo de la Tarifa
						cantidad	= product[0]	#Cantidad de Productos
						total = cantidad *  costo
						totalflete += total
						#Se crea el flete en la linea de fletes					
						vals_fl = {
									'liquidation_fletes':[(0,0,{'name': tarf[2],'id_flete':tarf[0] ,'price':costo ,'quantity':cantidad})]
								}
						#fl_obj.create(cr, uid, vals_fl)
						self.pool.get('liquidation.shipping').write(cr, uid, ids, vals_fl)	
						break
			#Monto Reconcido: se almacena el monto neto del flete 
			if totalflete > 0:
				self.pool.get('liquidation.shipping').write(cr, uid, ids, {'base_amount': totalflete})

		return True
		
	##guide_change----------------------------------------------------------------------------------------------------
	#Asignando Guia:
	#cuando se asigna la guia de despacho al flete, se obtienen otros valores automaticamente
	def guide_change(self, cr, uid, ids,guide):
		infoguide	= {}
		if not  guide:
			return {}
		infoguide = self.pool.get('delivery.guide').read(cr, uid, [guide], ['carrier_company_id','driver_id','warehouse_id','ruta_id','vehiculo_id'])[0]
		if infoguide:			
			res = {'value': {
									'carrier_company_id':infoguide['carrier_company_id'][0],
									'driver_id':infoguide['driver_id'][0],
									'warehouse_id':infoguide['warehouse_id'][0],
									'ruta_id':infoguide['ruta_id'][0],
									'vehiculo_id':infoguide['vehiculo_id'][0],											
				}} 
		return res
		return res


	##WORKFLOWS----------------------------------------------------------------------------------------------------
	#
	#				
	def wkf_confirm_liquidation(self, cr, uid, ids):
		obj_flete    = pooler.get_pool(cr.dbname).get('liquidation.shipping')
		flete    = obj_flete.browse(cr, uid, ids[0])
		idguide = flete.guide_id.id
		sql = "SELECT id FROM liquidation_shipping where guide_id=%d "%idguide
		cr.execute (sql)
		shipping_ids = cr.fetchall()
		for sp in shipping_ids:
		    if ids[0] != sp[0]:
		        raise osv.except_osv(_('Alerta :'),_('Guia ya procesada con otro flete!!!'))
		self.write(cr, uid, ids, {'state': 'confirmed'})
		self.pool.get('delivery.guide').write(cr, uid, [idguide], {'paid':True})
		return True	

	def wkf_cancel_liquidation(self, cr, uid, ids):
		self.write(cr, uid, ids, {'state': 'cancel'})
		return True	
						
liquidation_shipping()		
#-------------------------------------------------------------------------------------------------------------------------------------


#liquidation_shipping_line------------------------------------------------------------------------------------------------------------
#
class liquidation_shipping_line(osv.osv):
	_name = 'liquidation.shipping.line'
	_description = 'Liquidation Shipping line'	
	_columns = {
		'name': fields.char('Description', size=64),
		'sale_order': fields.char('Sale Order', size=64),
		'invoice_id': fields.many2one('account.invoice', 'Invoice Refund', required=True),
		'liquidation_id': fields.many2one('liquidation.shipping', 'Liquidation Ref', ondelete='cascade'),	
		'liquidation_esp': fields.boolean('Liquidacion Especial'),	 
	}

	_defaults = { }

	def liquidation_id_change(self, cr, uid, ids,invoice_id):
		res = {}			
		name_in = ''
		ref 	= '' 
		if not  invoice_id:
			return {}
			
		result_refund = self.pool.get('account.invoice').read(cr, uid, [invoice_id], ['reference','parent_id'])
		if result_refund and result_refund[0]:
			ref = result_refund[0]['reference']			
			if result_refund[0]['parent_id'] and result_refund[0]['parent_id'][0]:
				parent_id = result_refund[0]['parent_id'][0]
				name_in = self.pool.get('account.invoice').read(cr, uid, [parent_id], ['reference'])[0]['reference']
			res = {'value': {'name':ref,'sale_order':name_in}}  
		return res
		
liquidation_shipping_line()
#-------------------------------------------------------------------------------------------------------------------------------------


#liquidation_shipping_product_line------------------------------------------------------------------------------------------------------------
#
class liquidation_shipping_line_fl(osv.osv):
	_name = 'liquidation.shipping.line.fl'
	_description = 'Liquidation Shipping Fletes line'	
	_columns = {
		'name': fields.char('Description', size=64),
		'id_flete': fields.many2one('product.category.fle', 'Product'),
		'liquidation_ids': fields.many2one('liquidation.shipping', 'Liquidation Ref', ondelete='cascade'),	
		'price': fields.float('Price', digits=(16, int(config['price_accuracy']))),	 
		'quantity': fields.float('Price', digits=(16, 2)),
	}

	_defaults = { }
		
liquidation_shipping_line_fl()
#-------------------------------------------------------------------------------------------------------------------------------------
