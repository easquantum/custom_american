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

import string 
import time
import locale
from report import report_sxw
from osv import osv
import pooler

class summary_purchase_suppl(report_sxw.rml_parse):
	#Declaracion de Varables Globales--------------------------------------------------------------	
	tcompragral		= 0
	tivagral		= 0
	tcxpgral		= 0
	tcxcgral		= 0
	treservagral	= 0
	tprontopgral	= 0
	tctagral		= 0

	def __init__(self, cr, uid, name, context):
		super(summary_purchase_suppl, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'get_purchase': self._get_purchase,
			'get_totalgral_compra': self._get_totalgral_compra,
			'get_totalgral_iva': self._get_totalgral_iva,
			'get_totalgral_cxc': self._get_totalgral_cxc,	
			'get_totalgral_cxp': self._get_totalgral_cxp,	
			'get_totalgral_reserva': self._get_totalgral_reserva,
			'get_totalgral_prontop': self._get_totalgral_prontop,
			'get_totalgral_cta': self._get_totalgral_cta,	
			'get_warehouse': self._get_warehouse,
			'get_partner':self._get_partner,
		})

	def _get_purchase(self,form):
		#Inicializacion de variables---------------------------------------------------------------		
		resp = []
		self.tcompragral	= 0
		self.tivagral		= 0
		self.tcxpgral		= 0
		self.tcxcgral		= 0  
		self.treservagral	= 0
		self.tprontopgral	= 0
		self.tctagral		= 0
		
		fdesde		= form['date1']
		fhasta		= form['date2']
		proveedor	= form['supplierid']
		almacen		= form['warehouseid']	
		#Consulta Compras del periodo--------------------------------------------------------------	
		sql = """
		SELECT a.id,a.name,a.reference,a.number_document,SUM((l.price_standard * l.quantity_received)) AS total_standard, COALESCE(SUM(l.price_unit*l.quantity_received*(100-l.discount))/100.0,0)::decimal(16,4) AS total_unit
		FROM   account_invoice AS a 
		INNER  JOIN account_invoice_line AS l ON a.id=l.invoice_id
		WHERE  a.partner_id=%d AND a.type='in_invoice' AND a.state in ('open','paid') AND a.warehouse_id=%d  AND a.date_invoice BETWEEN '%s' AND '%s'
		GROUP  BY a.id,a.name,a.reference,a.number_document;"""%(proveedor,almacen,fdesde,fhasta)
		#print sql	 
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return []
			
		for invoice in resultSQL:
			total		= 0
			iva			= 0
			totalpp		= 0
			totalcta	= 0
			ttcxp		= 0
			cxc			= 0
			namecta		= ''
			ndeb		='N'
			ctarsv		='N'

			#Asignacion de datos de la factura de compras------------------------------------------
			nrocompra	= invoice[1]
			nrofact		= invoice[3]			
			totalcompra	= invoice[4]
			totalcxp	= invoice[5]
			ttcxp		= invoice[5]
			
			#Se consultan las Notas de Debito------------------------------------------------------
			sqlnd = """ 
			SELECT SUM(d.price_unit * d.quantity)	AS totalnd
			FROM		account_invoice 			AS a 
			INNER JOIN	account_invoice_line 		AS d ON a.id=d.invoice_id
			WHERE	a.type='in_refund' and a.parent_id=%d;"""%invoice[0]
			#print sqlnd
			self.cr.execute(sqlnd)
			resultND = self.cr.fetchall()
			if resultND and resultND[0] and resultND[0][0]:
				ndeb='S'
				for refund in resultND:
					#totalcxp -= refund[0] 
					cxc += refund[0]					
			totalreserva =  totalcompra - totalcxp - cxc
			#Se Consultan los Impuestos y/o Descuentos de las Facturas de Compra  
			tax_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice[0]) ]) 
			result_tax = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, tax_ids,['name', 'base','amount'])
			if not result_tax:
				totalcxp 		+= cxc
				totalreserva	+= cxc	
			
			#Procesando IMPUESTO-------------------------------------------------------------------
			#el grupo de debe ser del tipo 'vat' o IVA
			#de lo contrario no sera tomado como un Impuesto tipo IVA
			sqltax = """
			SELECT a.base,a.amount, t.name, t.amount     
			FROM 	account_invoice_tax AS a 
			INNER JOIN account_tax      AS t ON a.name=t.name
			WHERE t.tax_group='vat' AND  a.invoice_id=%d"""%invoice[0]
			self.cr.execute(sqltax)
			resultTAX = self.cr.fetchall()
			if resultTAX: 
				iva       = resultTAX[0][1]  #IVA
				totalcxp  = resultTAX[0][0]  #Base
			#Procesando DESCUENTOS-----------------------------------------------------------------
			#el valor del porcentaje debe estar con signo negativo 
			#de lo contrario no sera tomado como una Cta de Descuento
			sqldscto = """
			SELECT a.base,a.amount, t.name, t.amount, t.tax_group, t.sequence    
			FROM 	account_invoice_tax AS a 
			INNER JOIN account_tax      AS t ON a.name=t.name
			WHERE t.tax_group='other' AND t.amount < 0 AND  a.invoice_id=%d 
			ORDER BY t.sequence asc ;"""%invoice[0]
			self.cr.execute(sqldscto)
			result_dscto = self.cr.fetchall()
			if result_dscto: 
				#Se obtiene el monto de la Cta
				namecta		= result_dscto[0][2]
				totalcta	= result_dscto[0][1] *  -1
				#Si tiene nota de debito, se recalcula total de la cta
				#if ndeb=='S':
				#	totalcta = totalcompra * result_dscto[0][3] * -1
				totalreserva = 0
				ctarsv='S'
				#Se obtiene el monto Pronto Pago
				if len(result_dscto) > 1:
					totalpp   = result_dscto[1][1] *  -1
			#Totales Acumulados--------------------------------------------------------------------
			ttr = 0
			if totalcompra < totalcxp and ctarsv=='S':
			    totalreserva =  totalcxp - totalcompra
			else:
			    ttr = totalcxp + totalcta
			    totalreserva =  (totalcompra + cxc) - ttr
			self.tcompragral  += totalcompra
			self.tivagral     += iva
			self.tcxpgral     += totalcxp
			self.tcxcgral     += cxc
			self.treservagral += totalreserva
			self.tprontopgral += totalpp
			self.tctagral     += totalcta
			resp.append({"compra":nrocompra,"factura":nrofact,"totalcompra":totalcompra,"totaliva":iva,"cxc":cxc,"totalcxp":totalcxp,"reserva":totalreserva,"totalpp":totalpp,"cta":namecta,"totalcta":totalcta })			
		return resp


	def _get_totalgral_compra(self): 
		return self.tcompragral

	def _get_totalgral_iva(self): 
		return self.tivagral

	def _get_totalgral_cxc(self): 
		return self.tcxcgral

	def _get_totalgral_cxp(self): 
		return self.tcxpgral

	def _get_totalgral_reserva(self): 
		return self.treservagral

	def _get_totalgral_prontop(self): 
		return self.tprontopgral

	def _get_totalgral_cta(self): 
		return self.tctagral
						
	def _get_warehouse(self,warehouse):
		self.cr.execute ("""
								SELECT name
								FROM stock_warehouse
								WHERE id=%d;"""%warehouse)
		nwarehouse = self.cr.fetchall()
		return nwarehouse[0][0]

	def _get_partner(self,partner):
		self.cr.execute ("""
								SELECT name
								FROM res_partner
								WHERE id=%d;"""%partner)
		partner = self.cr.fetchall()
		namepartner = partner[0][0]
		return namepartner

report_sxw.report_sxw('report.summary_purchase_suppl','account.invoice','addons/custom_american/custom_account/report/summary_purchase_supplier.rml',parser=summary_purchase_suppl, header=False)
