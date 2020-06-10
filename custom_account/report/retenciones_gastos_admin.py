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

class retenciones_gadm(report_sxw.rml_parse):
	#Declaracion de Varables Globales--------------------------------------------------------------------------------------------
	ttimpuesto  = 0
	ttretencion = 0
	ttbase      = 0
	ttiva		= 0

	def __init__(self, cr, uid, name, context):
		super(retenciones_gadm, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'get_detalle': self._get_detalle,
			'get_mes': self._get_mes,	
			'get_totalgral_base': self._get_totalgral_base,		
			'get_totalgral_iva': self._get_totalgral_iva,
			'get_totalgral_rec': self._get_totalgral_rec,					
		})

	def _get_detalle(self, form):
		#Inicializacion Variables Locales---------------------------------------------------------------------------------------------------------
		result		= []
		alicuota	= 0
		iva			= 0
		impuesto	= 0
		total		= 0
		retenc		= 0
		cont		= 0
		fdesde		= form['date1']
		fhasta		= form['date2']
		
		#Consulta de las Compras Gastos Administrativos del periodo-------------------------------------------------------------------------------
		sql = """
		SELECT  a.id,a.name,a.date_document, a.number_document,a.number_control,p.ref, p.name,p.retention,p.id,a.amount_total,a.exentas  
		FROM       account_invoice 		AS a
		INNER JOIN res_partner			AS p ON a.partner_id=p.id
		WHERE a.no_sujetas=False AND a.state!='cancel' AND a.type='in_invoice_ad' AND a.date_invoice BETWEEN '%s' AND '%s'
		ORDER BY a.date_document;"""%(fdesde,fhasta) 
		#print sql
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"item":'',"compra":'', "fecha": '', "proveedor":'',"tipo":'', "nrofac":'',"nrocont":'',"codigo":'',"base":0,"alicuota":0,"iva":0,"retenc":0,"pretn":0}]
			 
		for invoice in resultSQL:
			#inicializacion de variables-----------------------------------------------------------------------------------------------
			alicuota	= 0
			base		= 0
			iva			= 0
			retenc		= 0
			razonsocial	= ''
			nrocomp		= invoice[1] 
			fecha		= invoice[2]
			nrofact		= invoice[3]
			nrocont		= invoice[4]
			codpro		= invoice[5]
			porcret		= invoice[7]
			partner_id	= invoice[8]
			#Se consulta la Razon Social del porveedor---------------------------------------------------------------------------------------------------
			partner 	= pooler.get_pool(self.cr.dbname).get('res.partner.address').search(self.cr, self.uid, [('partner_id','=',partner_id),('type','=','default') ])
			resultadd	= pooler.get_pool(self.cr.dbname).get('res.partner.address').read(self.cr, self.uid, partner,['name'])
			if 	resultadd:
				razonsocial	= resultadd[0]['name']
			else:
				razonsocial	= invoice[6]	
			if invoice[10]: 
				base = invoice[9]
			else:
				#Se consultan los Impuesto  -----------------------------------------------------------------------------------------------------------------
				tax_invoice_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice[0]) ])
				resulttax       = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, tax_invoice_ids,['name','base','amount'])
				if resulttax:
					for tax in resulttax:
						tax_id		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
						tax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])				
						if tax_info and tax_info[0]['tax_group'] == 'vat':
							alicuota	= tax_info[0]['amount'] * 100
							iva			= tax ['amount']
							base		= tax['base']	
							if porcret > 0:
								retenc = iva * porcret / 100 
			cont += 1
			result.append({"item":cont,"compra":nrocomp, "fecha": fecha, "proveedor":razonsocial,"tipo":'C', "nrofac":nrofact,"nrocont":nrocont,"codigo":codpro,"base":base,"alicuota":alicuota,"iva":iva,"retenc":retenc,"pretn":porcret})
			self.ttretencion	+= retenc
			self.ttbase			+= base
			self.ttiva			+= iva	

		return result


	def _get_mes(self,fecha):
		f= fecha.split('-')
		m = {'mes':f[1]}	
		return m['mes']

	def _get_totalgral_base(self): 
		return self.ttbase		

	def _get_totalgral_iva(self): 
		return self.ttiva		
		
	def _get_totalgral_rec(self): 
		return self.ttretencion		
		
report_sxw.report_sxw('report.retenciones_gastos_admin','account.invoice','addons/custom_american/custom_account/report/retenciones_gastos_admin.rml',parser=retenciones_gadm, header=False)
