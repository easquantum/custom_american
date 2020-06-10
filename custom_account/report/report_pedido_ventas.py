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
import locale

class pedido_venta(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	currentOrderId	= 0
	impuesto		= 0
	subtotal		= 0
	totalgral		= 0
	totalcajas		= 0
	pay				= 0
	product_cp		= []	
	#----------------------------------------------------------------------
	def __init__(self, cr, uid, name, context):
		super(pedido_venta, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 			
			'get_detalle': self._get_detalle,
			'get_notas_atencion': self._get_notas_atencion,
			'get_totaldcto': self._get_totaldcto,
			'get_terminopago': self._get_terminopago,
			'get_subtotal': self._get_subtotal,
			'get_total': self._get_total,
			'get_totalcajas': self._get_totalcajas,
			'get_vendedor': self._get_vendedor,
		})

	def _get_detalle(self, order):		
		if not order:
			return []

		resp = []
		#Inicializacion Variables Globales----------------------------------------------------
		if self.currentOrderId == 0 or self.currentOrderId != order:
			self.currentOrderId	= order
			self.totalgral		= 0
			self.subtotal		= 0
			self.totaldcto		= 0
			self.totalcajas		= 0
			self.pay			= 0
			product_fact		= []
			
		sql = """	
		SELECT  p.default_code,t.name,p.variants,s.price_unit,s.product_uom_qty,s.id   
		FROM	 sale_order_line		AS s
		LEFT     JOIN product_product	AS p  ON s.product_id=p.id
		INNER  JOIN product_template	AS t  ON p.product_tmpl_id=t.id  
		WHERE order_id=%d 
		ORDER BY p.default_code;"""%order		
		self.cr.execute (sql)
		resultSQL		= self.cr.fetchall()
		if not resultSQL:
			product_fact	= [{"cod":'',"nomb":'',"ref":'',"cant":0,"precio":0,"total":0,"alic":0}]
			
		for inf in resultSQL:
			total = 0
			iva   = 0 
			alic  = 0
			sqlt = """
			select t.amount 
			from sale_order_tax as s
			inner join account_tax as t on s.tax_id=t.id  
			where order_line_id=%d and t.tax_group='vat'
			"""%inf[5]
			self.cr.execute (sqlt)
			for tx in self.cr.fetchall():
			    if tx:
			        alic  = 100 * tx[0]

			#if inf[5]:
			#    alic  = 100 * inf[5]
			if (inf[3] > 0) and (inf[4] > 0):
				total = inf[3]*inf[4]
				self.totalcajas  += inf[4]
				self.subtotal += total						
			product_fact.append({"cod":inf[0],"nomb":inf[1],"ref":inf[2],"cant":inf[4],"precio":inf[3],"total":total,"alic":alic})	
		return product_fact		

	def _get_notas_atencion(self,order):
		notaline = ''
		sale	= pooler.get_pool(self.cr.dbname).get('sale.order').read(self.cr, self.uid, [order],['nota_atencion'])
		if sale and sale[0] and sale[0]['nota_atencion']:
			notaline = sale[0]['nota_atencion']
		sql = """	
		SELECT n.code,n.name 
		FROM	 sale_nota_atencion_rel     AS r
		INNER  JOIN nota_atencion           AS n	 ON r.nota_atencion_id=n.id
		WHERE r.sale_id=%d ;"""%order
		self.cr.execute (sql)
		rsp = []
		for nota in self.cr.fetchall():
			notaline += ' NA = ' + nota[0]
		return notaline
		
	def _get_terminopago(self,payterm):
		self.pay		= 0
		porc_dscto		= 0
		self.totaldcto	= 0
		sql = """	
		SELECT  t.amount  
		FROM	 account_payment_tax_rel     AS r
		INNER  JOIN account_tax              AS t	 ON r.tax_id=t.id
		WHERE r.paymenterm_id=%d ;"""%payterm
		self.cr.execute (sql)
		result = self.cr.fetchall()
		if result and result[0]:	
			porc_dscto = 	(result[0][0] * 100) * -1
			self.totaldcto = self.subtotal * porc_dscto / 100
			self.pay = porc_dscto
		return porc_dscto
					
	def _get_vendedor(self,id_zona):
	    if id_zona:
	        nomb = ''
	        sql = "SELECT name FROM res_partner WHERE salesman=True AND code_zone_id=%d"%id_zona
	        self.cr.execute (sql)
	        vendedor = self.cr.fetchall()
	        if vendedor and vendedor[0]:
	            nomb = vendedor[0][0]
	        return nomb
	            
	def _get_subtotal(self):
		return self.subtotal

	def _get_totalcajas(self):
		return self.totalcajas
		     
	def _get_total(self):
		self.totalgral = self.subtotal - self.totaldcto
		return self.totalgral

	def _get_totaldcto(self):
		return self.totaldcto		
		
report_sxw.report_sxw('report.pedido_venta','sale.order','addons/custom_american/custom_sale/report/report_pedido_ventas.rml',parser=pedido_venta, header=False)
