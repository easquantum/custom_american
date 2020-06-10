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

class liquidation_s(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	totalflete		= 0
	totalcajas		= 0
	dtotalflete		= 0
	dtotalcajas		= 0
	tarifas      	= []
	def __init__(self, cr, uid, name, context):
		super(liquidation_s, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_today': self._get_today,
			'get_invoices': self._get_invoices,
			'get_notas_credito': self._get_notas_credito,
			'set_totales': self._set_totales,
			'get_totalcajas': self._get_totalcajas,
			'get_totalflete': self._get_totalflete,
			'get_dtotalcajas': self._get_dtotalcajas,
			'get_dtotalflete': self._get_dtotalflete,
			'get_totalpagar': self._get_totalpagar,				
		})

	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today
		
	def _get_invoices(self,guide):
		self.totalflete = 0
		self.totalcajas = 0
		self.tarifas 	= []
		sql = """
		SELECT  d.invoice_id,p.ref,i.amount_total,SUM(quantity) as cajas,i.id,i.payment_term,i.number    
		FROM	delivery_guide_line    	 AS d
		INNER  JOIN account_invoice    	 AS i	 ON d.invoice_id=i.id
		INNER  JOIN account_invoice_line AS r	 ON i.id=r.invoice_id 
		INNER  JOIN res_partner        	 AS p	 ON i.partner_id=p.id 
		WHERE d.guide_id=%d
		GROUP BY d.invoice_id,p.ref,i.amount_total,i.id,i.payment_term,i.number 
		ORDER BY i.number;"""%guide
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"factura":'',"codigo":'',"totalcred":0,"totalcon":0,"cajas":0,"notas":''}]
			
		resp = []
		for invoice in resultSQL:	
			nc = ''
			idfact		= invoice[0]
			codcli		= invoice[1]
			cantidad	= invoice[3]
			notacred	= invoice[4]
			tipopago	= invoice[5]
			factnro		= invoice[6]
			credito		= 0
			contado		= 0
			#Factura
			#factura = self.pool.get('account.invoice').read(self.cr, self.uid,  [idfact], ['number'])
			#if factura and factura[0] and factura[0]['number']:
			#    factnro = factura[0]['number']
			
			refund_ids = pooler.get_pool(self.cr.dbname).get('account.invoice').search(self.cr, self.uid, [('parent_id','=',notacred) ])
			refund = self.pool.get('account.invoice').read(self.cr, self.uid,  refund_ids, ['name'])
			if refund and refund[0]:
				inf_refund = refund[0]
				if inf_refund['name']:
					nc = inf_refund['name']
			if tipopago:
				payment = pooler.get_pool(self.cr.dbname).get('account.payment.term').read(self.cr, self.uid, [tipopago],['contado'])
				if payment and payment[0]['contado']:
					contado	= invoice[2]
				else:
					credito	= invoice[2]			
			resp.append({"factura":factnro,"codigo":codcli,"totalcred":credito,"totalcon":contado,"cajas":cantidad,"notas":nc})
		return resp
		

	def _get_notas_credito(self,liquid):
		self.dtotalflete = 0
		self.dtotalcajas = 0				
		sqlnc = """	
		SELECT SUM(i.quantity) as cantidad,p.id_flete,l.invoice_id,l.name 
		FROM liquidation_shipping_line AS l 
		INNER JOIN account_invoice_line AS i ON l.invoice_id=i.invoice_id 
		INNER JOIN product_product AS p ON i.product_id=p.id 
		WHERE l.liquidation_id=%d 
		GROUP BY p.id_flete,l.invoice_id,l.name ;"""%liquid	
		self.cr.execute (sqlnc)
		respnc = []
		datnc = self.cr.fetchall()
		if not datnc:
			respnc.append({"factura":'',"notas":' ',"cajasnc":0,"tarifanc":0.00,"totalnc":0.00})
		for inf in datnc:
			costo = 0
			total   = 0
			fact   = inf[3]
			notacdnro = ''
			notacd = self.pool.get('account.invoice').read(self.cr, self.uid,  [inf[2]], ['name'])
			if notacd and notacd[0] and notacd[0]['name']:
			    notacdnro = notacd[0]['name']
			self.dtotalcajas += inf[0]
			for tarf in self.tarifas:
				if tarf[0] == inf[1]:
					costo = tarf[1] 
					total = inf[0] *  costo
					self.dtotalflete += total
					break	
			respnc.append({"factura":fact,"notas":notacdnro,"cajasnc":inf[0],"tarifanc":costo,"totalnc":total}) 
		#print "NC",respnc
		return respnc
		

	def _set_totales(self,tarf_id,cajas,precio):
		self.totalcajas += cajas
		self.totalflete += cajas * precio
		self.tarifas.append([tarf_id,precio])
		return

	def _get_totalcajas(self):
		return self.totalcajas	

	def _get_totalflete(self):
		return self.totalflete

	def _get_dtotalcajas(self):
		return self.dtotalcajas	

	def _get_dtotalflete(self):
		return self.dtotalflete

	def _get_totalpagar(self):
		totalpagar = self.totalflete - self.dtotalflete
		return totalpagar
										
report_sxw.report_sxw('report.liquidation_shipping','liquidation.shipping','addons/custom_american/credit_collection/report/report_liquidation.rml',parser=liquidation_s, header=False)
