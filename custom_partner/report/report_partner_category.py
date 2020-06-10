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

from report import report_sxw
from osv import osv
import pooler

class partner_bycategory(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(partner_bycategory, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_partner_information': self._get_partner_information,
		})
	
		
	def _get_partner_information(self,category_id,subcateg):
		resp = []
		if category_id: 
			ids_str = category_id
			if subcateg: 
				catg_ids = self.pool.get('res.partner.category').search(self.cr, self.uid, [('parent_id', 'child_of', [category_id])])			
				ids_str = ','.join(map(str,catg_ids))		 
			sql = """	
			SELECT	c.id,c.name,p.name,p.vat
			FROM		res_partner_category_rel AS r 
			INNER JOIN  res_partner AS p  ON r.partner_id=p.id 
			INNER JOIN res_partner_category AS c ON r.category_id=c.id   
			WHERE	r.category_id in ( %s ) 
			ORDER BY c.name,p.name;""" %ids_str
			#print sql  
			self.cr.execute(sql)
			catg_id = 0
			for reg in self.cr.fetchall():
				if catg_id==reg[0]: 
					resp.append({"catg":'',"nomb":reg[2],"rif":reg[3]})
				else:
					catg_id = reg[0]
					resp.append({"catg":reg[1],"nomb":reg[2],"rif":reg[3]})
		return resp

report_sxw.report_sxw('report.partner_by_category','res.partner','addons/custom_american/custom_partner/report/report_partner_category.rml',parser=partner_bycategory, header=False )
