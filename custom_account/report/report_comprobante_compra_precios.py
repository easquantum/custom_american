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
import locale
from report import report_sxw
from osv import osv
import pooler 

class comprobante_compra_precios(report_sxw.rml_parse):
	currentOrderId	= 0
	impuesto		= 0
	totalnd			= 0
	subtotal		= 0
	totalgral		= 0 
	
	def __init__(self, cr, uid, name, context): 
		super(comprobante_compra_precios, self).__init__(cr, uid, name, context)
		self.localcontext.update({ 
			'time': time,
			'locale': locale, 
			'get_det_order': self._get_det_order, 
			'get_impuestos_dsctos': self._get_impuestos_dsctos, 
			'get_notas_dedito': self._get_notas_dedito,
			'get_subtotal': self._get_subtotal, 
			'get_impuesto': self._get_impuesto,
			'get_total': self._get_total,
			'get_user_owner': self._get_user_owner, 
		})

	def _get_det_order(self, invoice):		
		if not invoice: 
			return []
		sql ="""
		SELECT p.default_code,s.product_code, t.name,p.variants,a.quantity,a.price_unit  
		FROM 	account_invoice_line		AS a
		INNER JOIN	product_product			AS p ON a.product_id=p.id
		INNER JOIN	product_template		AS t ON p.product_tmpl_id=t.id
		LEFT  JOIN 	product_supplierinfo	AS s ON t.id=s.product_id 															
		WHERE a.invoice_id=%d;"""%invoice
		self.cr.execute (sql)			
		resp = []
		for inf in self.cr.fetchall(): 
			total = 0 
			iva   = 0
			if self.currentOrderId == 0 or self.currentOrderId != invoice: 
				self.currentOrderId	= invoice
				self.totalgral		= 0
				self.subtotal		= 0
				self.impuesto		= 0
				self.totalnd		= 0
			
			if (inf[4] > 0) and (inf[5] > 0):
				total = inf[4]*inf[5]
				self.subtotal = self.subtotal + total				
											
			resp.append({"cod":inf[0],"codprov":inf[1],"nomb":inf[2],"ref":inf[3],"cant":inf[4],"precio":inf[5],"total":total})	

		return resp		
	
	def _get_impuestos_dsctos(self,invoice):

		# Get tax ids 
		orders_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice) ])

		# Get result
		result = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, orders_ids,['name', 'base','amount'])	
		#print result
		if result:
			for i in result:
				if i['amount'] < 0:
					self.impuesto += i['amount']
			return result
		else:
			return [{'amount': 0.00, 'base': 0.00, 'name': ' ', 'id': 0}]
		
	def _get_notas_dedito(self,nota_entrada): 

		# Get tax ids
		self.totalnd = 0
		nd_ids = pooler.get_pool(self.cr.dbname).get('account.invoice').search(self.cr, self.uid, [('parent_id','=',nota_entrada),('type','=','in_refund') ])
		resp = [] 
		if nd_ids:
			# Get result
			result = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, nd_ids,['reference','amount_total','amount_tax'])
			for nd in result: 
				ndmonto = nd['amount_total'] - nd['amount_tax']
				self.totalnd += ndmonto
				resp.append({"reference":nd['reference'],"total":ndmonto})	
			return resp 
		else:			
			return [{"reference":' ',"total":0.00}]		
		
		
	def _get_subtotal(self): 
		return self.subtotal
     
	def _get_total(self): 
		self.totalgral = self.subtotal + self.impuesto - self.totalnd
		return self.totalgral

	def _get_impuesto(self): 
		return self.impuesto
				
	def _get_user_owner(self,order):
		sql = """
		SELECT u.name  
		FROM account_invoice AS o
		JOIN res_users AS u 
		ON o.create_uid=u.id 															
		WHERE o.id=%d;"""%order
		self.cr.execute (sql)										
		username = self.cr.fetchall()
		return username[0][0]
					
report_sxw.report_sxw('report.comprobante_compra_precios','account.invoice','addons/custom_american/custom_account/report/report_comprobante_compra_precios.rml',parser=comprobante_compra_precios, header=False)
