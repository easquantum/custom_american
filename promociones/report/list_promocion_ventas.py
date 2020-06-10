# -*- encoding: utf-8 -*-
########################################################################################################
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
########################################################################################################

import time
import datetime
import locale
from report import report_sxw
from osv import osv
import pooler

class list_promo(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(list_promo, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_today': self._get_today,
            'list_promo': self._list_promo,
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today

    def _list_promo(self,form):
        data = [{'nro':'','cliente':'','fecha':'','zona':'','status':''}]
        if not form:
            return data
        fdesde = form['date1']
        fhasta = form['date2']
        tipo   = form['type']
        sql   = """
        SELECT s.name,s.date_promocion,p.name,z.name,s.state  
        FROM  sale_promocion         AS s
        INNER JOIN res_partner       AS p ON s.partner_id=p.id
        INNER JOIN res_partner_zone  AS z ON s.code_zone_id=z.id
        WHERE s.type='%s' AND s.date_promocion BETWEEN '%s' AND '%s' 
        ORDER BY s.date_promocion,s.partner_id """%(tipo,fdesde,fhasta)
        #print sql
        self.cr.execute(sql)
        list = self.cr.fetchall()
        if  list:
            data = []
            for l in list:
                data.append({"nro":l[0],"fecha":l[1],"cliente":l[2],'zona':l[3],"status":l[4]})
        return data

report_sxw.report_sxw('report.list_promocion','sale.promocion','addons/custom_american/promociones/report/list_promocion_ventas.rml',parser=list_promo, header=False)