# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Corvus Latinoamerica, C.A. 
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

from report import report_sxw
from osv import osv
import pooler
import time
import locale

class historico_p(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(historico_p, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,		
			'get_PartnerListPrice': self._get_PartnerListPrice,
		})					
				
	def _get_PartnerListPrice(self, product):
		result		= [{'proveedor':'No hay datos','precio':0,'fecha':''}]
 		if not product:
			return result 
		sql = """
		SELECT  s.id,a.name,r.price,r.date_order    
		FROM product_product 				AS p
		INNER JOIN product_template     	AS t  ON p.product_tmpl_id=t.id
		INNER JOIN product_supplierinfo	AS s  ON t.id=s.product_id 
		LEFT JOIN res_partner           		AS a  ON s.name=a.id 
		LEFT JOIN pricelist_partnerinfo 		AS r  ON s.id=suppinfo_id 
		WHERE p.id=%d 
		ORDER BY a.name,r.date_order desc;"""%product
		self.cr.execute(sql)
		datos =  self.cr.fetchall()
		tmp_id	= 0
		if datos:
			result		= []
			for inf in datos:
				if tmp_id==inf[0]:
					result.append({'proveedor':'','precio':inf[2],'fecha':inf[3]})
				else:
					tmp_id = inf[0]
					result.append({"proveedor":inf[1],"precio":inf[2],'fecha':inf[3]})
		return result
		     
report_sxw.report_sxw('report.historico_precios','product.product','addons/custom_altamira/custom_product/report/report_historico_precios.rml',parser=historico_p, header=False)      
