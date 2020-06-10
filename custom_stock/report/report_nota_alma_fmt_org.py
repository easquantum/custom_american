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
from report import report_sxw
from osv import osv
import pooler

class nota_almacen_fmt(report_sxw.rml_parse):
				
	def __init__(self, cr, uid, name, context):
		super(nota_almacen_fmt, self).__init__(cr, uid, name, context)		
		self.localcontext.update({
			'time': time,
			'get_nota': self._get_nota,
			'get_state':self._get_state,

		})
	
	def _get_nota(self, nota_id):	
		if not nota_id:
			return []
		self.cr.execute ("""
								SELECT 
											p.default_code,s.product_code, t.name,m.product_qty,p.variants  
								FROM 
											stock_move AS m
								INNER JOIN 
											product_product AS p	ON m.product_id=p.id
								INNER JOIN 
											product_template AS t 	ON p.product_tmpl_id=t.id
								LEFT JOIN 
											product_supplierinfo AS s ON t.id=s.product_id 															
								WHERE 
											picking_id=%d;"""%nota_id)
		resp = []		
		for inf in self.cr.fetchall():	
			resp.append({"cod":inf[0],"codprov":inf[1],"nomb":inf[2], "cntb":inf[3],"ref":inf[4]})
		return resp	
		
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

			
report_sxw.report_sxw('report.nota_almacen_fmt','stock.picking','addons/custom_american/custom_stock/report/report_nota_alma_fmt.rml',parser=nota_almacen_fmt, header=False)
