# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
import locale
from report import report_sxw
from osv import osv
import pooler


class nota_salida(report_sxw.rml_parse):
	tot_caj  = 0
	tot_peso = 0
				
	def __init__(self, cr, uid, name, context):
		super(nota_salida, self).__init__(cr, uid, name, context)		
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'get_nota': self._get_nota,
			'get_total':self._get_total,
			'get_total_peso':self._get_total_peso,
			'get_state':self._get_state,

		})
	
	def _get_nota(self, nota_id):
		self.tot_caj = 0
		self.tot_peso = 0	
		if not nota_id:
			return []
		sql = """
		SELECT p.default_code,s.product_code, t.name,m.product_qty,p.variants,p.id,weight_net   
		FROM stock_move AS m
		INNER JOIN	product_product AS p	ON m.product_id=p.id
		INNER JOIN	product_template AS t 	ON p.product_tmpl_id=t.id
		LEFT JOIN 	product_supplierinfo AS s ON t.id=s.product_id 															
		WHERE 	picking_id=%d
		ORDER BY p.default_code;"""%nota_id
		self.cr.execute (sql)
		resp = []		
		for inf in self.cr.fetchall():	
			#prod 	= pooler.get_pool(self.cr.dbname).get('product.product').read(self.cr,self.uid, [inf[5]],['qty_available'])
			#if prod and prod[0]: 
			#    existencia = prod[0]['qty_available']
			peso = 0
			if inf[6]: 
			    peso = inf[6] * inf[3] 
			resp.append({"cod":inf[0],"codprov":inf[1],"nomb":inf[2], "cntb":inf[3],"ref":inf[4],"peso":peso})
			self.tot_caj  += inf[3]
			self.tot_peso += peso
		return resp	
		
	def _get_total_peso(self):
	    return self.tot_peso

	def _get_total(self):
		return self.tot_caj

	def _get_state(self, state):
		estado = {
			'draft':'Disponible',
			'auto':'En espera',
			'confirmed':'Confirmado',
			'assigned':'Disponible',
			'done':'Realizado',
			'cancel':'Cancelar'
		}
		return estado[state]

			
report_sxw.report_sxw('report.nota_salida_almacen','stock.picking','addons/custom_american/custom_stock/report/report_nota_alma_salida.rml',parser=nota_salida, header=False)
