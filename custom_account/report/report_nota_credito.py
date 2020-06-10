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
from report import report_sxw
from osv import osv
import pooler
import locale

class nota_credit(report_sxw.rml_parse):
	address_delivery = []
	currentId = 0
	totaliva = 0
	iva		= 0
	subtotal = 0
	totalgral = 0
	totalcajas  = 0
	pay           = 0
	product_bof  = []
	product_cp  = [] 
	lblank = []	
	def __init__(self, cr, uid, name, context):
		super(nota_credit, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 	
			'get_address_partner': self._get_address_partner,
			'get_address_delivery': self._get_address_delivery,		
			'get_detalle': self._get_detalle,
			'get_subtotal': self._get_subtotal,
			'get_total': self._get_total,
			'get_totalcajas': self._get_totalcajas,
			'get_date_order': self._get_date_order,
			'set_blank_line': self._set_blank_line,
			'get_blank_line': self._get_blank_line,
			'get_iva': self._get_iva,
			'get_totaliva': self._get_totaliva,
			'get_vendedor': self._get_vendedor,
		})

	def _set_blank_line(self, nlines):
		res = ""
		self.lblank = []
		for i in range(25 - nlines):
			res = res + '\n'
			self.lblank.append({'lineb':'.'})
		return 
		
	def _get_detalle(self, invoice):		
		if not invoice:
			return [{"cod":0,"nomb":'',"ref":'',"cant":0,"precio":0,"total":0,"alicota":0}] 
		if self.currentId == 0 or self.currentId != invoice:
			#Inicializacion Variables-----------------------------------------------------------------------------------------
			self.currentId		= invoice
			self.totalgral		= 0
			self.subtotal		= 0
			self.totaldcto		= 0
			self.totalcajas		= 0
			self.pay			= 0
			self.iva 			= 0			
			cont 				= 0
			resDet				= []
		#Productos de la factura------------------------------------------------------------------------------------------
		sql = """	
		SELECT  p.default_code,t.name,p.variants,l.quantity,l.price_unit,l.id   
		FROM	account_invoice_line		AS l
		LEFT    JOIN product_product		AS p	ON l.product_id=p.id
		INNER   JOIN product_template		AS t	ON p.product_tmpl_id=t.id
		WHERE invoice_id=%d 
		ORDER BY p.default_code;"""%invoice
		self.cr.execute(sql)		
		resultSQL = self.cr.fetchall()		 
		if not resultSQL:
			return [{"cod":0,"nomb":'',"ref":'',"cant":0,"precio":0,"total":0,"alicuota":0}]
		for invoice in resultSQL:
			total	= 0 
			iva		= 0
			cont	+= 1
			alicuota = 0
			cod		= invoice[0]
			product	= invoice[1]
			referen	= invoice[2]
			cant	= invoice[3]
			precio	= invoice[4]
			det_id	= invoice[5] 
			if (cant > 0) and (precio > 0):
				total = cant * precio
				self.totalcajas  += cant
				self.subtotal += total		
			#validar si el producto tiene iva 
			sqltax = """	
			SELECT  t.tax_group,t.amount    
			FROM  account_invoice_line_tax AS a
			INNER JOIN account_tax AS t ON a.tax_id=t.id
			WHERE invoice_line_id=%d and t.tax_group='vat';"""%det_id	
			self.cr.execute (sqltax)
			tax = self.cr.fetchall()
			if tax:
				alicuota = tax[0][1] * 100
				self.iva = alicuota
			else:
				referen += '  (E)'
				
			resDet.append({"cod":cod,"nomb":product,"ref":referen,"cant":cant,"precio":precio,"total":total,"alicuota":alicuota})
		self._set_blank_line(cont) 
		return resDet		

	def _get_blank_line(self):
		return self.lblank 
      
	def _get_address_partner(self,partner):
		self.address_delivery = []
		sql = """	SELECT a.street,a.street2,a.phone,s.name,c.name
							FROM	 res_partner_address     AS a 
							INNER  JOIN   res_country_state    AS s	 ON a.state_id=s.id 
							INNER  JOIN   res_state_city    AS c ON a.city_id=c.id 
							WHERE a.type='delivery' AND a.partner_id=%d ;"""%partner
		self.cr.execute (sql)
		result = self.cr.fetchall()
		if result:
			self.address_delivery = result[0]	 	
		return 

	def _get_vendedor(self,zona):
		vendedor = ''
		sql = "SELECT name FROM	res_partner WHERE active=True AND salesman=True AND code_zone_id=%d ;"%zona
		self.cr.execute (sql)
		result = self.cr.fetchall()
		if result:
			vendedor = result[0][0]	 	
		return vendedor

	def _get_date_order(self,pedido):
		fecha = ''
		pedido_id = pooler.get_pool(self.cr.dbname).get('sale.order').search(self.cr, self.uid, [('name','=',pedido) ])
		if pedido_id:
			pedido = pooler.get_pool(self.cr.dbname).get('sale.order').read(self.cr, self.uid, pedido_id,['date_order'])		
			fecha = pedido[0]['date_order'] 	
		return fecha

	def _get_address_delivery(self):
		return  self.address_delivery
					
	def _get_subtotal(self):
		return self.subtotal

	def _get_totalcajas(self):
		return self.totalcajas

	def _get_iva(self):
		return self.iva
		
	def _get_totaliva(self):
		self.totaliva = self.subtotal * self.iva / 100
		return self.totaliva
		
	def _get_total(self):
		self.totalgral = self.subtotal + self.totaliva
		return self.totalgral
	
report_sxw.report_sxw('report.nota_credito','account.invoice','addons/custom_american/custom_account/report/report_nota_credito.rml',parser=nota_credit, header=False)
