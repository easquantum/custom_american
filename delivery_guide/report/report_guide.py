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

class delivery_g(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	totalpeso = 0
	totalcajas = 0
	#----------------------------------------------------------------------
	def __init__(self, cr, uid, name, context):
		super(delivery_g, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_today': self._get_today,
			'get_guide_line': self._get_guide_line,
			'get_product_line': self._get_product_line,
			'get_totalcajas': self._get_totalcajas,
			'get_totalpeso': self._get_totalpeso
		})

	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today
		
	def _get_guide_line(self,guide):
		sql = """	
		SELECT  i.name,i.payment_term,p.ref,p.name,z.code_zone,i.check_total,SUM(quantity) as cajas  
		FROM	delivery_guide_line			AS d
		INNER  JOIN account_invoice			AS i	 ON d.invoice_id=i.id
		INNER  JOIN account_invoice_line	AS r	 ON i.id=r.invoice_id 
		INNER  JOIN res_partner				AS p	 ON i.partner_id=p.id
		LEFT   JOIN res_partner_zone		AS z  ON p.code_zone_id=z.id 
		WHERE d.guide_id=%d
		GROUP BY i.name,i.payment_term,p.ref,z.code_zone,p.name,i.check_total ;"""%guide
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"factura":'',"codigo":'',"nomb":'',"zona":'',"totalcontado":0,"totalcredito":0,"cajas":0}]		
		resp = []
		for inf in resultSQL:			
			#Asignacion de Variables---------------------------------------------------------------------------------
			factnro	= inf[0]
			tipopago= inf[1]
			codcli	= inf[2]
			nombcli	= inf[3]
			zona	= inf[4]
			contado	= 0
			credito	= 0
			cajas	= inf[6]
			#Tipo de Condicion de Pago------------------------------------------------------------------------------
			if tipopago:
				payment = pooler.get_pool(self.cr.dbname).get('account.payment.term').read(self.cr, self.uid, [tipopago],['contado'])
				if payment and payment[0]['contado']:
					contado	= inf[5]
				else:
					credito	= inf[5]
			resp.append({"factura":factnro,"codigo":codcli,"nomb":nombcli,"zona":zona,"totalcontado":contado,"totalcredito":credito,"cajas":cajas})
		return resp
		
	def _get_product_line(self,guide):
		self.totalpeso = 0
		self.totalcajas = 0
		sqlp = """
		SELECT  p.default_code,s.product_code,t.name,p.variants,SUM(r.quantity) AS cantidad,t.weight_net  
		FROM	delivery_guide_line    	 AS d
		INNER  JOIN account_invoice_line AS r	 ON d.invoice_id=r.invoice_id
		INNER  JOIN product_product 	 AS p	 ON r.product_id=p.id
		INNER  JOIN product_template 	 AS t	 ON p.product_tmpl_id=t.id
		LEFT  JOIN  product_supplierinfo AS s ON t.id=s.product_id
		WHERE d.guide_id=%d
		GROUP BY p.default_code,s.product_code,t.name,p.variants,t.weight_net 
		ORDER BY p.default_code ;"""%guide
		self.cr.execute (sqlp)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"codigoadv":'',"codigopv":'',"producto":'',"referencia":'',"cajas":0,"peso":0}]
		rsp = []
		for inf in resultSQL:
			peso = 0		
			if inf[5]: 
				peso += inf[5] * inf[4]
				self.totalpeso += peso	
			rsp.append({"codigoadv":inf[0],"codigopv":inf[1],"producto":inf[2],"referencia":inf[3],"cajas":inf[4],"peso":peso}) 
			self.totalcajas += inf[4]

		return rsp
		
	def _get_totalcajas(self):
		return self.totalcajas	

	def _get_totalpeso(self):
		return self.totalpeso
						
report_sxw.report_sxw('report.delivery_guide','delivery.guide','addons/custom_american/delivery_guide/report/report_guide.rml',parser=delivery_g, header=False)
