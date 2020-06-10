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

class comprobante_compra(report_sxw.rml_parse):
	currentOrderId	= 0
	subtotal		= 0
	totalgral		= 0
	totalnd			= 0
	totalcxp		= 0
	r				= 'N'
	totales			= []
	#locale.setlocale(locale.LC_ALL,'es_VE.utf8')	
	
	def __init__(self, cr, uid, name, context):
		super(comprobante_compra, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time, 
			'locale': locale,  
			'get_det_order': self._get_det_order,
			'get_subtotal': self._get_subtotal, 
			'get_notas_dedito': self._get_notas_dedito, 
			'get_total': self._get_total,
			'get_total_cxp': self._get_total_cxp,
			'get_total_nd': self._get_total_nd, 
			'get_totales': self._get_totales,			
			'get_items': self._get_items,
			'get_total_reserva': self._get_total_reserva,			
			'get_user_owner': self._get_user_owner, 
		})

	def _get_det_order(self, order):		
		if not order:
			return []
		sql = """
		SELECT	d.name,d.quantity_received,d.price_unit,d.discount,d.price_standard  
		FROM	account_invoice_line AS d
		WHERE	invoice_id=%d
		ORDER	BY d.id;"""%order
		self.cr.execute (sql)
		resp = [] 
		for inf in self.cr.fetchall():
			total	= 0
			totalcs	=0
			desc	= 0 
			if self.currentOrderId == 0 or self.currentOrderId != order:
				self.currentOrderId = order
				self.subtotal		= 0
				self.totalgral		= 0
				self.totalnd		= 0
				self.subtotalcs		= 0
				self.totalcxp		= 0
			if (inf[1] > 0) and (inf[2] > 0):
				total = inf[1]*inf[2]
				totalcs = inf[1]*inf[4]
				if inf[3] > 0:
					desc = total * inf[3] /100
					total -=  desc
				self.subtotal	+=  total							
				self.subtotalcs	+= totalcs
								
			resp.append({"nomb":inf[0],"cant":inf[1],"preciop":inf[2],"precios":inf[4],"totalS":totalcs,"totalP":total})		
		#Reserva 
		self.totalreserva = self.subtotalcs - self.subtotal		
		return resp		
		
	def _get_subtotal(self):
		return self.subtotal
     
	def _get_total(self): 
		return {'totalgralP':self.subtotal,'totalgralS':self.subtotalcs}

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
				self.totalnd -= ndmonto
				resp.append({"reference":nd['reference'],"total":ndmonto})	
		
		if result: 
			return resp
		else:			
			return []	
		
	def _get_total_cxp(self): 
		return self.totalcxp 
		
	def _get_totales(self):
		self.totales       = {'base':self.totalgral,'iva':self.totalimpuesto}
		return self.totales
		
	def _get_items(self):
		return self.r

	def _get_total_nd(self): 
		return self.totalnd
				
	def _get_total_reserva(self):
		self.totalreserva += self.totalnd
		return self.totalreserva 
						
	def _get_user_owner(self,order):
		self.cr.execute ("""
								SELECT u.name  
								FROM account_invoice AS o
								JOIN res_users AS u 
								ON o.create_uid=u.id 															
								WHERE o.id=%d;"""%order)										
		username = self.cr.fetchall()
		return username[0][0]				

report_sxw.report_sxw('report.comprobante_compra','account.invoice','addons/custom_american/custom_account/report/report_comprobante_compra.rml',parser=comprobante_compra, header=False)
