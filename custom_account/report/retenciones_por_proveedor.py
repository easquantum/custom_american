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
import datetime
import locale
from report import report_sxw
from osv import osv
import pooler

class retentionsbysupplier(report_sxw.rml_parse):
	#Inicializacion de Variables Globales--------------------------------------------------------------------
	ttimpuesto	= 0
	ttretencion	= 0
	ttbase		= 0
	ttiva		= 0
	ttotal		= 0
	ttotalsin	= 0
	
	def __init__(self, cr, uid, name, context):
		super(retentionsbysupplier, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'get_today': self._get_today,
			'get_periodo':self._get_periodo,
			'get_detalle': self._get_detalle,
			'get_partner': self._get_partner,
			'get_company': self._get_company,
			'get_cod_retenc': self._get_cod_retenc,
			'get_address_company':self._get_address_company,
			'get_mes': self._get_mes,	
			'get_totalgral_base': self._get_totalgral_base,		
			'get_totalgral_iva': self._get_totalgral_iva,
			'get_totalgral_rec': self._get_totalgral_rec,
			'get_totalgral_con': self._get_totalgral_con,	
			'get_totalgral_sin': self._get_totalgral_sin,					
		})

	def _get_detalle(self, form):
		#inicializacion de variables Locales-----------------------------------------------------------------
		result		= []
		alicuota	= 0
		iva			= 0
		impuesto	= 0
		total		= 0
		retenc		= 0
		cont		= 0
		fdesde		= form['date1']
		fhasta		= form['date2']
		partner		= form['supplierid']
		
		#Consulta de las Compras Gastos Administrativos del periodo------------------------------------------------------------------			
		sql = """
		SELECT  a.id,a.date_document, a.number_document,a.number_control,p.retention   
		FROM     account_invoice	AS a
		INNER JOIN res_partner		AS p ON a.partner_id=p.id
		WHERE a.exentas=False AND a.no_sujetas=False AND a.state!='cancel' AND a.type in ('in_invoice_ad','in_invoice') AND a.date_invoice BETWEEN '%s' AND '%s' AND a.partner_id=%d
		ORDER BY a.date_document;"""%(fdesde,fhasta,partner) 
		print sql 
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		print "SQL",resultSQL
		if not resultSQL:
			return [{"item":'',"fecha": '',"tipo":'', "nrofac":'',"nrocont":'',"notac":'',"afectada":'',"totalconiva":0,"totalsin":0,"base":0,"alicuota":0,"iva":0,"retenc":0}]
				
		for invoice in resultSQL:
			#Inicializacion de Variables---------------------------------------------------------------------------------------------- 
			base		= 0
			iva			= 0
			retenc		= 0
			total		= 0	
			totalsin	= 0 
			fecha		= invoice[1]
			nrofact		= invoice[2]
			nrocont		= invoice[3]
			porcret		= invoice[4]			
			cont		+= 1
			#Se consultan los Impuesto  -----------------------------------------------------------------------------------------------------------------
			tax_invoice_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice[0]) ])
			resulttax       = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, tax_invoice_ids,['name','base','amount'])
			if resulttax: 
				for tax in resulttax:
					#Se Obtiene el Grupo o tipo de Tax-----------------------------------------------------------------------------
					tax_id		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
					tax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])
					if tax_info[0]['tax_group'] == 'vat':
						alicuota	= tax_info[0]['amount'] * 100
						iva			= tax['amount']
						base		= tax['base']	
						total		= base + iva
						if porcret > 0:
							retenc = iva * porcret / 100 		
			
			#Consultar productos sin impuestos----------------------------------------------------------------------------------------
			sqlsin ="""
			SELECT SUM(a.price_unit * a.quantity) AS totalsin  
			FROM account_invoice_line AS a 
			WHERE invoice_id=%d  AND a.id 
			NOT IN (SELECT t.invoice_line_id FROM  account_invoice_line_tax AS t WHERE a.id = t.invoice_line_id) """%invoice[0]
			self.cr.execute (sqlsin)
			dats = self.cr.fetchall()
			if dats[0][0]:
				totalsin = dats[0][0]	
			result.append({"item":cont, "fecha": fecha,"tipo":'C', "nrofac":nrofact,"nrocont":nrocont,"notac":'',"afectada":'',"totalconiva":total,"totalsin":totalsin,"base":base,"alicuota":alicuota,"iva":iva,"retenc":retenc})
			
			#Totales-------------------------------------------------------------------------------------------------------------------			
			self.ttretencion	+= retenc
			self.ttbase			+= base
			self.ttiva			+= iva	
			self.ttotal			+= total
			self.ttotalsin		+= totalsin
			
			#Se Consultan Notas de Debito------------------------------------------------------------------------------------------------- 
			notasdeb_ids = pooler.get_pool(self.cr.dbname).get('account.invoice').search(self.cr, self.uid, [('type','=','in_refund'),('parent_id','=',invoice[0])])
			result_notasdeb = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, notasdeb_ids,['id','date_document','number_document','number_control'])
			for nd in result_notasdeb:
				nd_id	= nd['id']
				ndnro	= nd['number_document']
				ndnroc	= nd['number_control']
				ndfecha	= nd['date_document']
				#Se Consultan los Impuesto de la Nota Debito---------------------------------------------------------------------------			
				ndtax_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',nd_id) ])
				result_ndtax = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, ndtax_ids,['name','base','amount'])				
				for ndtax in ndtax_ids:
					ndretenc	= 0
					ndiva		= 0
					ndbase		= 0  
					ndtotal		= 0 
					#Se Obtiene el Grupo o tipo de Tax---------------------------------------------------------------------------------
					tax_ids		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',ndtax['name']) ])
					tax_inf	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_ids,['tax_group','amount'])
					if tax_inf[0]['tax_group'] == 'vat':
						cont	+= 1
						ndiva	= ndtax['amount'] 
						ndbase	= ndtax['base']  
						ndtotal	= ndbase + ndiva
						
						if porcret > 0:
							ndretenc = ndiva * porcret / 100
						self.ttretencion	-= ndretenc
						self.ttbase			-= ndbase
						self.ttiva			-= ndiva
						self.ttotal			-= ndtotal	
						result.append({"item":cont, "fecha": ndfecha,"tipo":'NC', "nrofac":'',"nrocont":ndnroc,"notac":ndnro,"afectada":nrofact,"totalconiva":ndtotal,"totalsin":0,"base":ndbase,"alicuota":alicuota,"iva":ndiva,"retenc":ndretenc})
		return result

	def _get_partner(self,partner):
		res  = pooler.get_pool(self.cr.dbname).get('res.partner').read(self.cr, self.uid, [partner],['name','vat'])
		datos     = res[0]
		#Se Consulta la Razon Social del Proveedor----------------------------------------------------------------------------------
		add_id = pooler.get_pool(self.cr.dbname).get('res.partner.address').search(self.cr, self.uid, [('partner_id','=',partner),('type','=','default') ])
		resp  = pooler.get_pool(self.cr.dbname).get('res.partner.address').read(self.cr, self.uid, add_id,['name'])
		if resp:
			address = resp[0]
			datos['name'] =  address['name'] 
		return datos

	def _get_company(self): 
		sql = """ SELECT c.name,p.vat	 
						  FROM res_company AS c
						  INNER JOIN res_partner AS p ON  c.partner_id=p.id ;"""
		self.cr.execute (sql) 
		datos = self.cr.fetchall()
		company = datos[0]
		return company 

	def _get_address_company(self): 
		self.cr.execute (""" SELECT d.street,d.street2, d.phone 
							 					FROM res_company AS c
						 					 	INNER JOIN res_partner AS p ON  c.partner_id=p.id
							 					INNER JOIN  res_partner_address AS d ON p.id=d.partner_id;""")
							 					
		datos = self.cr.fetchall()
		dir = datos[0][0] + "  " + datos[0][1] + "    Telf: " + datos[0][2]
		return dir
		
	def _get_mes(self,fecha):
		f= fecha.split('-')
		m = {'mes':f[1]}	
		return m['mes']

	def _get_periodo(self,fecha):
		f= fecha.split('-')
		periodo = {'a':f[0],'m':f[1]}	
		return periodo
		
	def _get_totalgral_base(self): 
		return self.ttbase		

	def _get_totalgral_iva(self): 
		return self.ttiva		
		
	def _get_totalgral_rec(self): 
		return self.ttretencion		

	def _get_totalgral_sin(self): 
		return self.ttotalsin
			
	def _get_totalgral_con(self): 
		return self.ttotal	
						
	def _get_cod_retenc(self,partner,fecha):
		partner  = pooler.get_pool(self.cr.dbname).get('res.partner').read(self.cr, self.uid, [partner],['ref'])
		codigo     = partner[0]['ref'] 
		f= fecha.split('-')
		if int(f[2]) >15:
			periodo = '30'
		else:
			periodo = '15'	
		
		codpartner = codigo.zfill(6)
		numero_comp = f[0]+f[1]+periodo+codpartner
		return numero_comp	 
		
	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today
						
report_sxw.report_sxw('report.retenciones_por_proveedor','account.invoice','addons/custom_american/custom_account/report/retenciones_por_proveedor.rml',parser=retentionsbysupplier, header=False)
