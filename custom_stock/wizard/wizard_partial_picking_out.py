##############################################################################
#
# Copyright (c) 2007-2009 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved.
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
import netsvc
from tools.misc import UpdateableStr
import pooler

import wizard
from osv import osv
from osv.osv import except_osv

_moves_arch = UpdateableStr()
_moves_fields = {}

_moves_arch_end = '''
<?xml version="1.0"?>
<form string="Picking Result"><label string="La Nota Salida Fue Procesada Correctamente !" colspan="4" />
</form>'''
_moves_fields_end = {}

listmv = {}

def make_default(val):
	def fct(uid, data, state):
		return val
	return fct

def _get_moves(self, cr, uid, data, context):
	pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	pick = pick_obj.browse(cr, uid, [data['id']])[0]
	res = {}
	self.listp = []
	_moves_fields.clear()
	_moves_arch_lst = ['<?xml version="1.0"?>', '<form string="Notas Salida">']
	fecha = time.strftime('%Y-01-01')
	fini  = time.strftime('%Y-%m-01')
	ffin  = time.strftime('%Y-%m-%d')
	mes   = int(fini[5:7])
	if mes == 1:
	    a = int(fini[:4]) 
	    newy = a -1
	    fecha = str(newy)+'-01-01'
	cierre_id = 0 
	almacen_org_id  = pick.warehouse_id.id
	dpsto_id = pick.warehouse_id.lot_stock_id.id
	sqli = "SELECT id,name FROM stock_inventory WHERE warehouse_id=%d AND date >'%s' ORDER BY id;"%(almacen_org_id,fecha)
	cr.execute (sqli)
	cierre = cr.fetchall()
	if cierre:
	    ind = len(cierre)
	    if ind > 0:
	        ind -=1
	        cierre_id = cierre[ind][0]

	for m in pick.move_lines:
		quantity = m.product_qty
		#if m.state<>'assigned':
		#	quantity = 0
		_moves_arch_lst.append('<field name="move%s" />' % (m.id,))
		#Validar existencias
		invent_inicial = 0
		existencia_act = 0
		prod_id        = m.product_id.id
		inventory_line_id = pooler.get_pool(cr.dbname).get('stock.inventory.line').search(cr, uid, [('inventory_id','=',cierre_id),('product_id', '=', prod_id) ])
		if inventory_line_id:
		    invent_inicial = pooler.get_pool(cr.dbname).get('stock.inventory.line').read(cr, uid, inventory_line_id,['total_real_qty'])[0]['total_real_qty']  
		sqlp = """ 
		SELECT SUM((g.entradas - g.salidas)) AS existencia 
		FROM(
		    SELECT 
		    SUM(COALESCE(sm.product_qty,0)) AS entradas, COALESCE(0) AS salidas 
		    FROM       stock_picking      AS sp 
		    INNER JOIN stock_move         AS sm ON sp.id=sm.picking_id 
		    INNER JOIN product_product    AS pp ON sm.product_id=pp.id 
		    WHERE sp.type='in' AND sp.warehouse_id=%d AND sp.state='done' AND pp.id=%d 
		    AND sp.date_done  BETWEEN '%s' AND '%s 24:00'
		    UNION  SELECT 
		    COALESCE(0) AS entradas,SUM(COALESCE(sm.product_qty,0)) AS salidas 
		    FROM       stock_picking      AS sp 
		    INNER JOIN stock_move         AS sm ON sp.id=sm.picking_id
		    INNER JOIN product_product    AS pp ON sm.product_id=pp.id 
		    WHERE sp.type='out' AND sp.warehouse_id=%d AND sp.state='done' AND pp.id=%d 
		    AND sp.date_done  BETWEEN '%s' AND '%s 24:00' 
		    UNION  SELECT 
		    SUM(COALESCE(sm.product_qty,0)) AS entradas,COALESCE(0) AS salidas 
		    FROM       stock_picking      AS sp 
		    INNER JOIN stock_move         AS sm ON sp.id=sm.picking_id
		    INNER JOIN product_product    AS pp ON sm.product_id=pp.id 
		    WHERE sp.type='internal' AND sp.warehouse_id=%d AND sm.location_dest_id=%d AND sp.state='done' AND pp.id=%d 
		    AND sp.date_done  BETWEEN '%s' AND '%s 24:00'
		    UNION  SELECT 
		    SUM(COALESCE(sm.product_qty,0)) AS entradas,COALESCE(0) AS salidas 
		    FROM       stock_picking      AS sp 
		    INNER JOIN stock_move         AS sm ON sp.id=sm.picking_id
		    INNER JOIN product_product    AS pp ON sm.product_id=pp.id 
		    WHERE sp.type='internal' AND sp.warehouse_dest_id=%d AND sm.location_dest_id=%d AND sp.state='done' AND pp.id=%d 
		    AND sp.date_done  BETWEEN '%s' AND '%s 24:00'
		    UNION  SELECT 
		    COALESCE(0) AS entradas,SUM(COALESCE(sm.product_qty,0)) AS salidas 
		    FROM       stock_picking      AS sp 
		    INNER JOIN stock_move         AS sm ON sp.id=sm.picking_id
		    INNER JOIN product_product    AS pp ON sm.product_id=pp.id 
		    WHERE sp.type='internal' AND sp.warehouse_id=%d AND sm.location_id=%d AND sp.state='done' AND pp.id=%d 
		    AND sp.date_done  BETWEEN '%s' AND '%s 24:00'
		) AS g
		"""%(almacen_org_id,prod_id,fini,ffin,almacen_org_id,prod_id,fini,ffin,almacen_org_id,dpsto_id,prod_id,fini,ffin,almacen_org_id,dpsto_id,prod_id,fini,ffin,almacen_org_id,dpsto_id,prod_id,fini,ffin) 
		#print sqlp
		#if  almacen_org_id ==1:
		if  almacen_org_id in (1,2,3,4):
		    cr.execute (sqlp)
		    existencia = cr.fetchall()
		    existencia_act = invent_inicial
		    if existencia and existencia[0] and existencia[0][0]:
		        existencia_act += existencia[0][0]
		existencia_act = str(existencia_act)
		listmv['move%s' %m.id] = existencia_act
		_moves_fields['move%s' % m.id] = {'string' : '%s - %s - %s - EXISTENCIA:---> (%s)' % (m.product_id.code, m.product_id.name, m.product_id.variants,existencia_act), 'type' : 'float', 'required' : True, 'default' : make_default(quantity)}
		if (pick.type == 'in') and (m.product_id.cost_method == 'average'):
			price=0
			if hasattr(m, 'purchase_line_id') and m.purchase_line_id:
				price=m.purchase_line_id.price_unit
			currency=0
			if hasattr(pick, 'purchase_id') and pick.purchase_id:
				currency=pick.purchase_id.pricelist_id.currency_id.id
			_moves_arch_lst.append('<group><field name="price%s"/>' % (m.id,))
			_moves_fields['price%s' % m.id] = {'string': 'Unit Price', 'type': 'float', 'required': True, 'default': make_default(price)}
			_moves_arch_lst.append('<field name="currency%d"/></group>' % (m.id,))
			_moves_fields['currency%s' % m.id] = {'string': 'Currency', 'type': 'many2one', 'relation': 'res.currency', 'required': True, 'default': make_default(currency)}
		_moves_arch_lst.append('<newline/>')
		res.setdefault('moves', []).append(m.id)
	_moves_arch_lst.append('</form>')
	_moves_arch.string = '\n'.join(_moves_arch_lst)
	return res

def _do_print(self, cr, uid, data, context):
	pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	pick = pick_obj.browse(cr, uid, [data['id']])[0]
	if pick.type=='out':
		return 'print'
	return 'end'
def _do_split(self, cr, uid, data, context):
	move_obj = pooler.get_pool(cr.dbname).get('stock.move')
	pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	pick = pick_obj.browse(cr, uid, [data['id']])[0]
	new_picking = None
	new_moves = []
	almacen_org_id = pick.warehouse_id.id

	complete, too_many, too_few = [], [], []
	pool = pooler.get_pool(cr.dbname)
	#raise wizard.except_wizard('UserError', 'Prueba.!')
	cont_item = 0
	move_item = len(pick.move_lines)
	for move in move_obj.browse(cr, uid, data['form'].get('moves',[])):
		if float(data['form']['move%s' % move.id]) < 0:
		    # Nota:  No se permite cantidades en Negativo en las notas de salida.
		    raise wizard.except_wizard('UserError', 'No se pueden procesar Notas, No se permiten cantidades en Negativo.!')
		#if almacen_org_id == 1: 
		if almacen_org_id in (1,2,3,4): 
		    if float(data['form']['move%s' % move.id]) > float(listmv['move%s' % move.id]):
			    if float(listmv['move%s' % move.id]) < 0:
			        data['form']['move%s' % move.id] = 0
			    else:
			        data['form']['move%s' % move.id] = listmv['move%s' % move.id]
			    #print "move.product_qty",move.product_qty,"QTYDATAF",data['form']['move%s' % move.id]
		if float(data['form']['move%s' % move.id]) <= 0:
		    cont_item += 1
		if float(move.product_qty) == float(data['form']['move%s' % move.id]):
			complete.append(move)
		elif float(move.product_qty) > float(data['form']['move%s' % move.id]):
			too_few.append(move)
		else:
			#too_many.append(move)
			# Nota:  No se permite cantidades mayores para los productos en las notas de salida.
			raise wizard.except_wizard('UserError', 'No se pueden procesar Notas, que tengan productos con cantidades Mayores a las del Pedido!')
	# Nota:  lista de movimientos con los productos que no se recibieron.
	if almacen_org_id ==1 and move_item == cont_item:
	    raise wizard.except_wizard('UserError', 'No se puede procesar la Nota, los productos no poseen existencia disponible.')
	empty = []
	for move in too_few: 
		if not new_picking:
			new_picking = pick_obj.copy(cr, uid, pick.id, 
				{
					'backorder':True,
					'name' : pool.get('ir.sequence').get(cr, uid, 'stock.picking.%s' % pick.type + '_' + pick.type2),
					'move_lines' : [],
					'backorder_id':pick.id, 
					'state':'draft'
				})
#			pick.write(cr, uid, [pick.id], {'backorder_id' : new_picking})
		new_obj = move_obj.copy(cr, uid, move.id, 
			{
				'product_qty' : float(move.product_qty) - float(data['form']['move%s' % move.id]), 
				'product_uos_qty': float(move.product_qty) - float(data['form']['move%s' % move.id]), 
				'picking_id' : new_picking, 
				'state': 'assigned', 
				'move_dest_id': False,
				'price_unit': move.price_unit
			})
		# Nota:  Crea lista de movimientos con los productos que no se recibieron.
		if float(data['form']['move%s' % move.id]) == 0:
			empty.append(move.id)
			continue

		move_obj.write(cr, uid, [move.id], 
			{
				'product_qty' : data['form']['move%s' % move.id], 
				'product_uos_qty':data['form']['move%s' % move.id]
			})
	# Nota:  Se Valida que los productos que no se recibieron no se registren con monto "0" en la nota.
	if empty:
		move_obj.write(cr, uid, empty, {'product_qty' : 0, 'product_uos_qty':0, 'state':'draft'})
		op = 2
		value = False
		lst_mov = [(op,m,value) for m in empty]
		pick_obj.write(cr, uid, [pick.id], {'move_lines' : lst_mov})
		
	if complete:
	    move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': pick.id})

	# At first we confirm the new picking (if necessary)
	wf_service = netsvc.LocalService("workflow")
	# Then we finish the good picking
	try:
		if new_picking:
			wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
			# Nota:  Se cancela la Nota con los productos no despachados.
			wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_cancel', cr)
			pick_obj.action_move(cr, uid, [pick.id])
			#Se Cambia de Estatus las lineas de la nota
			wf_service.trg_validate(uid, 'stock.picking',pick.id , 'button_done', cr)
			#Se Cambia de Estatus la nota
			wf_service.trg_validate(uid, 'stock.picking',pick.id , 'button_done', cr)
			wf_service.trg_write(uid, 'stock.picking', new_picking, cr)
		else:
			pick_obj.action_move(cr, uid, [pick.id])
			#Se Cambia de Estatus las lineas de la nota
			wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
			#Se Cambia de Estatus la nota
			wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
	except except_osv, e:
		raise wizard.except_wizard(e.name, e.value)
	return {}

class custom_picking_out(wizard.interface):

	states = {
		'init' : {
			'actions' : [ _get_moves ],
			'result' : { 'type' : 'form', 'arch' : _moves_arch, 'fields' : _moves_fields, 'state' : (('end', 'Cancelar'),('split', 'Procesar Nota') )},
		},
		'split': {
			'actions': [_do_split],
			'result': {'type': 'state', 'state': 'end'},
		},
	}

custom_picking_out('partial_picking_out')
