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
from report import report_sxw
from osv import osv
import pooler
import locale


class comisiones_venta_div(report_sxw.rml_parse):
    #Variables Globales----------------------------------------------------
    currentId	= 0
    total	= 0

    def __init__(self, cr, uid, name, context):
		super(comisiones_venta_div, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'get_total': self._get_total,
			'get_total_por_vendedor': self._get_total_por_vendedor,
			'get_mes': self._get_mes,
			'get_year': self._get_year,
		})
       
    def _get_total(self):
        return self.total

    def _get_total_por_vendedor(self,divis,periodo):
        zone_ids = pooler.get_pool(self.cr.dbname).get('res.partner.zone').search(self.cr, self.uid, [('parent_id','=',divis)])
        if zone_ids:
            ids_str = ','.join(map(str,zone_ids))
        self.total = 0
        sql = """
        SELECT z.name,sale_total  
        FROM commissions_seller as c 
        INNER JOIN res_partner_zone as z ON c.zone_id=z.id      
        WHERE  c.commission_period_id=%d AND c.zone_id in (%s) 
        ORDER BY z.name;"""%(periodo,ids_str)
        #print sql
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        resp = []
        for z in datos:
            resp.append({"vendedor":z[0],"zona":z[0],"monto":z[1]})
            self.total += z[1]
        return resp

    def _get_mes(self,code):
        meses	= (['01','ENERO'],['02','FEBRERO'],['03','MARZO'],['04','ABRIL'],['05','MAYO'],['06','JUNIO'],['07','JULIO'],['08','AGOSTO'],['09','SEPTIEMBRE'],['10','OCTUBRE'],['11','NOVIEMBRE'],['12','DICIEMBRE'])
        mp  = ''
        mes = ''
        if code:
            mp = code.strip()
        for m in meses:
            if m[0] == mp:
                mes	= m[1]
        return mes


    def _get_year(self,fecha):
        year = ''
        if fecha:
            year  = fecha[0:4]
        return year 

report_sxw.report_sxw('report.commissions_sale_div','commissions.seller','addons/custom_american/custom_sale/report/report_commissions_seller_div.rml',parser=comisiones_venta_div, header=False)
