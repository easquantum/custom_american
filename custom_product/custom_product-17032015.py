# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Corvus Latinoamerica, C.A. 
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
logger = netsvc.Logger()
from osv import fields,osv,orm
from tools import config


#------------------------------------------------------------------------
#Categoria Comision Vendedores: 
#------------------------------------------------------------------------

class product_category_salesman(osv.osv): 
    _name = 'product.category.salesman'
    _description = 'Categoria Comision Vendedores'	
    _columns = {
    	'name': fields.char('Category', size=64, required=True),
    	'description': fields.char('Description', size=200),		
    }
    _defaults = {}
product_category_salesman()

class product_category(osv.osv):
	_inherit = 'product.category'
	_columns = {
		'code' : fields.char('Code', size=64),
	}

product_category()



class product_product(osv.osv):
	_inherit = 'product.product'

	def _get_cost_pub(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['publ_price'], context)
		res = []
		for record in reads:
			res.append((record['id'], record['publ_price']))
		return res

	def _get_porc(self, cr, uid, ids, field, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, [field], context)
		res = []
		for record in reads:
			res.append((record['id'], record[field]))
		return res	

	def _compute_price_disc(self, price, disc):
		return price * (1.0-(disc or 0.0))

	def _get_supplier_cost(self, cr, uid, ids, product_id, partner_id, context={}):
		product = self.browse(cr, uid, [product_id], context)[0]
		for supinfo in product.seller_ids:
			if not partner_id:
				return {'adv_cos': supinfo.name.adv_cos}
			if supinfo.name.id == partner_id:
				return {'adv_cos': supinfo.name.adv_cos}
		return {'adv_cos': False}

	def _compute_price_incr(self, price, incr):
		if incr==1:
			return price 
		return price * (1/(1.0-(incr or 0.0)))

	def _get_std_price(self, cr, uid, ids, name, args, context={}):
		res={}
		for id in ids:
			res.setdefault(id, 0.0)
			prec_publ = self._get_cost_pub(cr, uid, [id], context)[0][1]
			porc_d_pro=self._get_porc(cr, uid, [id], 'supp_disc', context)[0][1]/100
			res[id]=self._compute_price_disc(prec_publ,porc_d_pro)
			has_cos=self._get_supplier_cost(cr, uid, [], id, context.get('partner_id', None), context)
			if has_cos['adv_cos']:
				porc_i_adv=self._get_porc(cr, uid, [id], 'adv_marg', context)[0][1]/100
				res[id]=self._compute_price_incr(res[id],porc_i_adv)
		return res

	def _get_supp_price(self, cr, uid, ids, name, args, context):
		res={}
		for id in ids:
			res.setdefault(id, 0.0)
			prec_publ = self._get_cost_pub(cr, uid, [id], context)[0][1]
			porc_d_pro=self._get_porc(cr, uid, [id], 'supp_disc', context)[0][1]/100
			res[id]=self._compute_price_disc(prec_publ,porc_d_pro)
			self.pool.get('product.template').write(cr, uid, [id], {'standard_price': res[id]})	
		return res

	def _get_invo_price(self, cr, uid, ids, name, args, context):
		res={}
		for id in ids:
			res.setdefault(id, 0.0)
			prec_publ = self._get_cost_pub(cr, uid, [id], context)[0][1]
			porc_d_pro=self._get_porc(cr, uid, [id], 'supp_disc', context)[0][1]/100
			res[id]=self._compute_price_disc(prec_publ,porc_d_pro)
			porc_i_adv=self._get_porc(cr, uid, [id], 'adv_marg', context)[0][1]/100
			res[id]=self._compute_price_incr(res[id],porc_i_adv)
			has_cos=self._get_supplier_cost(cr, uid, [], id, context.get('partner_id', None), context)
			if has_cos['adv_cos']:
				porc_d_adv=self._get_porc(cr, uid, [id], 'adv_disc', context)[0][1]/100				
				res[id]=self._compute_price_incr(res[id],porc_d_adv)
			self.pool.get('product.template').write(cr, uid, [id], {'list_price': res[id]})
		return res

	def _product_dispo(self, cr, uid, ids, name, arg, context={}):
		res = {}
		out = self._product_outgoing_qty(cr, uid, ids, name, arg, context)
		now = self._product_qty_available(cr, uid, ids, name, arg, context)
		for p_id in ids:
			res[p_id] = now[p_id] + out[p_id]
		return res

	def _check_ean_key(self, cr, uid, ids):
	    return True
	
	_columns = {
		'publ_price': fields.float('Public Price', digits=(16, int(config['price_accuracy']))),
		'supp_disc': fields.float('Supplier Discount', digits=(6,3)),
		'adv_marg': fields.float('ADV Margin', digits=(6,3)),
		'adv_disc': fields.float('ADV. Discount', digits=(6,3)),
		'supp_price': fields.function(_get_supp_price, digits=(16,int(config['price_accuracy'])), method=True, string='Supplier Price'),
		'invo_price': fields.function(_get_invo_price, digits=(16,int(config['price_accuracy'])), method=True, string='Invoice Price'),
		'cost_price': fields.function(_get_std_price, digits=(16,int(config['price_accuracy'])), method=True, string='Cost Std. Price'),
		'pat_id': fields.many2many('product.category', 'pat_category_rel', 'product_id', 'pate_id', 'Patentes'),
		'group_id': fields.many2many('product.category', 'group_category_rel', 'product_id', 'grp_id', 'Group'),
		'qty_dispo': fields.function(_product_dispo, method=True, type='float', string='Stock available', help="Cantidad disponible para este Producto segun la ubicacion selecionada o todas las internas si no se ha seleccionado ninguna. Calculado como: Stock Real - Saliente."),
		'pick_val': fields.boolean('Picking valorado'),
		'qty' : fields.float('Quantity by Package'),
		'categ_salesman_id': fields.many2one('product.category.salesman', 'Product Category Salesman'),
		'account_reserv_id': fields.many2one('account.account', 'Account Reserva'),
		'promocion': fields.boolean('Promocion'),
	}
	_constraints = [(_check_ean_key, 'Error: Invalid ean code', ['ean13'])]	
	_defaults = {		
		'promocion': lambda *a: False,

	}

	def set_price_history(self, cr, uid, ids, dval, value, context):
		lst_seller  = []			
		lst_price   = []
		data_price  = {}
		dic_seller = {}
		dic_price  = {}

		data_price={
					'price': value['publ_price'], 
					'sup_price': value['supp_price'], 
					'inv_price': value['invo_price'], 
					'cos_price': value['cost_price'],
					'date_ope':time.strftime('%Y-%m-%d %H:%M:%S'),
					'min_quantity': 1.0,
					'name': value['supp_price'],
					}

		lst_price.append((0,0,data_price))
		if dval['seller_ids']:
			lst_seller = dval['seller_ids']
			tup_seller = lst_seller[0]
			dic_price = tup_seller[2]
			dic_price['pricelist_ids'] = lst_price
			tup_seller2 = (tup_seller[0], tup_seller[1], dic_price)
			lst_seller2 = [tup_seller2]
			dic_seller['seller_ids'] = lst_seller2
		if value['seller_ids']:
			dic_price['pricelist_ids'] = lst_price
			dic_seller['seller_ids'] = [(1 , value['seller_ids'][0] ,dic_price )]
		return dic_seller

	def create(self, cr, uid, vals, context=None):
		camp_list=['publ_price','supp_disc','adv_marg','adv_disc']
		for camp in camp_list:
			if camp in vals:
				del vals[camp]
		return super(product_product, self).create(cr, uid, vals,context=context)

	def write(self, cr, uid, ids, vals, context=None):
		camp_list=['publ_price','supp_disc','adv_marg','adv_disc']
		field_list=['publ_price','supp_price','invo_price','cost_price','seller_ids']
		chang=False

		data = self.read(cr, uid, ids, fields=field_list, context=context)[0]
		if vals.has_key('seller_ids') and  not vals['seller_ids'] and not data['seller_ids']:
			raise osv.except_osv('ERROR	', '¡Producto sin Proveedor!')

		for camp in camp_list:
			if camp in vals:
				chang=True
				break
		if chang:			
			vals.update(self.set_price_history(cr, uid, ids, vals, data, context))
		return super(product_product, self).write(cr, uid, ids, vals, context=context)

product_product()



class pricelist_partnerinfo(osv.osv):
	_inherit = 'pricelist.partnerinfo'	
	_columns = {		
		'sup_price': fields.float('supplier price', digits=(16, int(config['price_accuracy']))),
		'inv_price': fields.float('invoice price', digits=(16, int(config['price_accuracy']))),
		'cos_price': fields.float('cost std. price', digits=(16, int(config['price_accuracy']))),
		'date_ope':fields.datetime('date opened'),
										
	}
	_defaults = {		
	}
	_order = "date_ope desc"

pricelist_partnerinfo()
