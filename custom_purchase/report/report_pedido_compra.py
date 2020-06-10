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


import time
from report import report_sxw
from osv import osv
import pooler

class pedido_compra(report_sxw.rml_parse): 
	sum_total = 0
	ttcntf = 0
	ttcntb = 0	
				
	def __init__(self, cr, uid, name, context):
		super(pedido_compra, self).__init__(cr, uid, name, context)		
		self.localcontext.update({
			'time': time,
			'get_det_order': self._get_det_order,
			'get_total': self._get_total,
			'get_user_owner': self._get_user_owner
		})
	
	def _get_det_order(self, order):	
		if not order:
			return []
		sql = """
		SELECT	p.default_code,s.product_code, t.name,d.product_qty,p.variants  
		FROM 	purchase_order_line AS d
		INNER JOIN	product_product AS p	ON d.product_id=p.id
		INNER JOIN	product_template AS t 	ON p.product_tmpl_id=t.id
		LEFT JOIN 		product_supplierinfo AS s ON t.id=s.product_id 															
		WHERE 		   d.order_id=%d
		ORDER BY d.id;"""%order
		self.cr.execute (sql)
		resp = []		
		cntf   = 0
		self.ttcntf = 0
		self.ttcntb = 0
		for inf in self.cr.fetchall():	
			cntf = 	inf[3]							
			resp.append({"cod":inf[0],"codprov":inf[1],"nomb":inf[2],"cntf": cntf, "cntb":0,"cnttotal":inf[3],"ref":inf[4]})
			self.sum_total += inf[3]	
			self.ttcntf  += cntf
		return resp	 
		
	def _get_total(self):
		totales={'total_f':self.ttcntf,'total_b':self.ttcntb,'total':self.sum_total}
		return totales	
	
	def _get_user_owner(self,order): 
		self.cr.execute ("""
								SELECT u.name  
								FROM purchase_order AS o
								JOIN res_users AS u 
								ON o.create_uid=u.id 															
								WHERE o.id=%d;"""%order)	
		username = self.cr.fetchall()
		return username[0][0] 
			
report_sxw.report_sxw('report.pedido_compra','purchase.order','addons/custom_american/custom_purchase/report/report_pedido_compra.rml',parser=pedido_compra, header=False)
