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

class libro_iva_compras_gest(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	ttcompra	= 0
	ttretencion	= 0
	ttbase		= 0
	ttiva		= 0
	ttexento	= 0
	#---------------------------------------------------------------------
	def __init__(self, cr, uid, name, context):
		super(libro_iva_compras_gest, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_ivacompras': self._get_ivacompras, 
			'get_totalgral_compra': self._get_totalgral_compra,
			'get_totalgral_base': self._get_totalgral_base,
			'get_totalgral_rectencion': self._get_totalgral_rectencion,
			'get_totalgral_iva': self._get_totalgral_iva,
			'get_totalgral_exento': self._get_totalgral_exento,
			'get_company':self._get_company,
		})

	def _get_ivacompras(self, form):
		#inicializacion de variables Globales-------------------------------------------------------
		self.ttcompra		= 0
		self.ttretencion	= 0
		self.ttbase			= 0
		self.ttiva			= 0	
		self.ttexento		= 0
		#inicializacion de variables Locales-------------------------------------------------------------------------------------------
		result		= []
		alicuota	= 0		
		cont		= 0
		fdesde		= form['date1']
		fhasta		= form['date2']
		#Se Consultas las facturas de Compra correspondientes al periodo---------------------------------------------------------------					
		sql = """
		SELECT  a.id, a.name, a.date_document, a.number_document, a.number_control, p.vat, p.name, a.p_ret, a.amount_total    
		FROM    account_invoice AS a
		INNER JOIN res_partner AS p ON a.partner_id=p.id
		WHERE  state in ('open','paid') AND type='in_invoice' AND date_invoice BETWEEN '%s' AND '%s'
		ORDER BY a.date_document;"""%(fdesde,fhasta) 
		#print sql		
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"nro":0,"compra":'',"fecha":'', "rif":'', "proveedor":'', "nrofac":'', "nrocont":'' ,"afect":'',"total":0,"base":0,"alicuota":0,"iva":0,"exento":0,"retenc":0}]
		
		for invoice in resultSQL:
			#inicializacion de variables-----------------------------------------------------------------------------------------------
			base		= 0
			iva			= 0
			total		= 0
			exento		= 0
			retenc		= 0
			alicuota	= 0
			idinvoice	= invoice[0]
			nrocomp		= invoice[1] 
			fecha		= invoice[2]
			nrofact		= invoice[3]
			nrocont		= invoice[4]
			rifprov		= invoice[5]
			razonsocial	= invoice[6]
			porcret		= invoice[7]
			amountotal	= invoice[8]
			sinimpuesto = False 

			#Se consultan los Impuesto y/o descuentos -----------------------------------------------------------------------------------------------		
			tax_invoice_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',idinvoice) ])
			resulttax       = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, tax_invoice_ids,['name','base','amount'])
			if not resulttax:
				sinimpuesto =  True
			else:
				#Se descartan los descuentos y otros impuestos diferente del tipo 'vat' o  IVA  
				sinimpuesto =  True
				#Consulta de Productos EXENTOS-----------------------------------------------------------------------------------------------
				#Se valida si la factura posee productos exentos de impuesto			
				sqlsin="""
							SELECT SUM(a.price_unit * a.quantity) AS total  
							FROM account_invoice_line AS a 
							WHERE invoice_id=%d  AND a.id 
							NOT IN (SELECT t.invoice_line_id  FROM  account_invoice_line_tax AS t 	WHERE a.id = t.invoice_line_id);"""%idinvoice
				self.cr.execute (sqlsin)
				rslt = self.cr.fetchall()
				if rslt[0][0]:
					exento			=  rslt[0][0]
					self.ttexento	+= exento
				for tax in resulttax:
					#Se consulta el Grupo o tipo de Tax-----------------------------------------------------------------------------------------
					#los impuestos correspondientes al IVA, deben pertenecer al tipo 'vat'
					#para poder ser procesados correctamente
					tax_id		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
					tax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])
					#Procesar FACTURAS CON  IMPUESTOS-------------------------------------------------------------------------------------------					
					if tax_info[0]['tax_group'] == 'vat':
						sinimpuesto = False
						alicuota	= tax_info[0]['amount'] * 100
						iva			= tax['amount']
						base		= tax['base']
						total		= base + iva
						cont		+= 1		
						if porcret > 0:
							retenc = iva * porcret / 100
						result.append({"nro":cont,"compra":nrocomp,"fecha":fecha, "rif": rifprov, "proveedor":razonsocial, "nrofac":nrofact, "nrocont":nrocont ,"afect":'',"total":total,"base":base,"alicuota":alicuota,"iva":iva,"exento":exento,"retenc":retenc})
						self.ttcompra		+= total + exento
						self.ttretencion	+= retenc
						self.ttbase			+= base
						self.ttiva			+= iva
						exento				= 0

			#Procesar FACTURAS SIN  IMPUESTOS-------------------------------------------------------------------------------------
			if sinimpuesto:
				exento			= amountotal
				total			= amountotal
				self.ttexento	+= exento 
				self.ttcompra	+= total
				cont			+= 1
				result.append({"nro":cont,"compra":nrocomp,"fecha":fecha, "rif": rifprov, "proveedor":razonsocial, "nrofac":nrofact, "nrocont":nrocont ,"afect":'',"total":total,"base":base,"alicuota":alicuota,"iva":iva,"exento":exento,"retenc":retenc})
			#Procesar Notas Debito-------------------------------------------------------------------------------------------	
			nd_ids = pooler.get_pool(self.cr.dbname).get('account.invoice').search(self.cr, self.uid, [('type','=','in_refund'),('parent_id','=',idinvoice),('state','in',['open','paid']) ])			
			if nd_ids:
				for nd in nd_ids:
					ndbase		= 0
					ndiva		= 0
					ndtotal		= 0
					ndretenc	= 0	
					sinimpuesto = False
					notad 	= pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, nd_ids,['date_document','number_document','number_control','name'])[0]
					ndfecha = notad['date_document']
					ndnro   = notad['number_document']
					ndnroc  = notad['number_control']
					notadeb = notad['name']
					if ndnro and ndnroc and ndfecha:
						ndtax_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',nd) ])
						ndreslt = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, ndtax_ids,['name','base','amount'])
						if not ndtax_ids:
							sinimpuesto = True
						else:
							sinimpuesto =  True
							for ndt in ndreslt:
								ndtax_id		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',ndt['name']) ])
								ndtax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, ndtax_id,['tax_group','amount'])
								#Procesar FACTURAS CON  IMPUESTOS-------------------------------------------------------------------------------------------					
								if ndtax_info[0]['tax_group'] == 'vat':
									sinimpuesto = False
									alicuota	= ndtax_info[0]['amount'] * 100
									ndiva	= ndt['amount']
									ndbase	= ndt['base']
									ndtotal	= ndbase + ndiva
									if porcret > 0:
										ndretenc = ndiva * porcret / 100
									cont	+= 1
									result.append({"nro":cont,"fecha":ndfecha, "rif": rifprov, "proveedor":razonsocial, "nrofac":ndnro,"afect":nrofact,"nrocont":ndnroc,"total":ndtotal,"base":ndbase,"alicuota":alicuota,"iva":ndiva,"retenc":ndretenc,"exento":0,"compra":notadeb})
									self.ttcompra		-= ndtotal
									self.ttretencion	-= ndretenc
									self.ttbase			-= ndbase
									self.ttiva			-= ndiva
							#print "Result",result
		return result

	def _get_totalgral_compra(self): 
		return self.ttcompra

	def _get_totalgral_base(self): 
		return self.ttbase 
		
	def _get_totalgral_iva(self): 
		return self.ttiva

	def _get_totalgral_rectencion(self): 
		return self.ttretencion 
		
	def _get_totalgral_exento(self): 
		return self.ttexento		
				
	def _get_company(self):
		self.cr.execute (""" SELECT name	 FROM res_company;""")
		datos = self.cr.fetchall()
		company = datos[0][0]
		return company 


report_sxw.report_sxw('report.libro_iva_compras_gestion','account.invoice','addons/custom_american/custom_account/report/libro_iva_compras_gestion.rml',parser=libro_iva_compras_gest, header=False)
