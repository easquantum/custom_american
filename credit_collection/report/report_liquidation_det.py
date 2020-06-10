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

class liquidation_det(report_sxw.rml_parse):
	totalflete  = 0
	totalcajas = 0
	def __init__(self, cr, uid, name, context):
		super(liquidation_det, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_product_line': self._get_product_line,
			'get_totalcajas': self._get_totalcajas,
			'get_totalflete': self._get_totalflete
		})

		
	def _get_product_line(self,guide,ruta,vh):
		self.totalflete = 0
		self.totalcajas = 0				
		sqlg = """	
		SELECT  r.category_fle_id,r.price,c.name 
		FROM guide_ruta_line AS r
		INNER JOIN product_category_fle AS c ON r.category_fle_id=c.id
		WHERE r.ruta_id=%d AND r.tipo_vehiculo_id=%d ;"""%(ruta,vh) 
		self.cr.execute (sqlg)		
		datos_tarifa = self.cr.fetchall()

		sqlp = """	
		SELECT SUM(i.quantity) as cantidad,p.id_flete,p.default_code    
		FROM delivery_guide_line AS l 
		INNER JOIN account_invoice_line AS i ON l.invoice_id=i.invoice_id 
		INNER JOIN product_product AS p ON i.product_id=p.id 
		WHERE l.guide_id=%d 
		GROUP BY p.id_flete,p.default_code ;"""%guide							
		self.cr.execute (sqlp)
		resultSQL = self.cr.fetchall() 
		#print datos
		resptar = []
		for inf in resultSQL:
			costo = 0
			total   = 0
			self.totalcajas += inf[0]
			for tarf in datos_tarifa:
				if tarf[0] == inf[1]:
					costo = tarf[1] 
					total = inf[0] *  costo
					self.totalflete += total
					break	
			resptar.append({"code":inf[2],"cajas":inf[0],"tarifa":costo,"total":total}) 
			#self.totalcajas += inf[4]
		return resptar
		
	def _get_totalcajas(self):
		return self.totalcajas	

	def _get_totalflete(self):
		return self.totalflete
						
report_sxw.report_sxw('report.liquidation_detail','liquidation.shipping','addons/custom_american/credit_collection/report/report_liquidation_det.rml',parser=liquidation_det, header=False)
