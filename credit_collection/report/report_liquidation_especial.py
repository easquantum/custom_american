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
import datetime
import locale
from report import report_sxw
from osv import osv
import pooler

class liquidation_spec(report_sxw.rml_parse):
	totalflete		= 0
	totalcajas		= 0
	dtotalflete	= 0
	dtotalcajas	= 0
	tarifas      	= []
	def __init__(self, cr, uid, name, context):
		super(liquidation_spec, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_today': self._get_today,
			'get_notas_credito': self._get_notas_credito,
			'get_dtotalcajas': self._get_dtotalcajas,
			'get_dtotalflete': self._get_dtotalflete,			
		})

	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today
		

	def _get_notas_credito(self,liquid,ruta,vh):		
		sqlg = """	
		SELECT  id_flete,price,name 
		FROM liquidation_shipping_line_fl
		WHERE liquidation_ids=%d ;"""%(liquid)
		self.cr.execute (sqlg)		
		datos_tarifas = self.cr.fetchall()
			
		self.dtotalflete = 0
		self.dtotalcajas = 0				
		sqlnc = """
		SELECT a.name,SUM(i.quantity) as cantidad,p.id_flete,a.parent_id 
		FROM liquidation_shipping_line AS l
		INNER JOIN account_invoice AS a ON l.invoice_id=a.id  
		INNER JOIN account_invoice_line AS i ON l.invoice_id=i.invoice_id 
		INNER JOIN product_product AS p ON i.product_id=p.id 
		WHERE l.liquidation_id=%d AND l.liquidation_esp=True  
		GROUP BY p.id_flete,a.name,a.parent_id  ;"""%liquid	
		self.cr.execute (sqlnc)		
		#print self.tarifas
		respnc	= []
		vtarifa		= ''
		for inf in self.cr.fetchall():
			costo = 0
			total   = 0
			self.dtotalcajas += inf[1]
			for tarf in datos_tarifas:
				if tarf[0] == inf[2]:
					costo = tarf[1] 
					total = inf[1] *  costo
					vtarifa = tarf[2] + ':   ' + str(costo)
					self.dtotalflete += total
					break
			factnum = ''	
			if inf[3]:
				infoin = self.pool.get('account.invoice').read(self.cr, self.uid, [inf[3]], ['name',])[0]
				factnum= infoin['name']
			respnc.append({"factura":factnum,"notacred":inf[0] ,"cajas":inf[1],"tarifas":vtarifa,"total":total})  
		return respnc
		
			
	def _get_dtotalcajas(self):
		return self.dtotalcajas	

	def _get_dtotalflete(self):
		return self.dtotalflete

										
report_sxw.report_sxw('report.liquidation_especial','liquidation.shipping','addons/custom_american/credit_collection/report/report_liquidation_especial.rml',parser=liquidation_spec, header=False)
