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

class promo(report_sxw.rml_parse):
    total = 0
    cant  = 0
    def __init__(self, cr, uid, name, context):
        super(promo, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_today': self._get_today,
            'get_vendedor': self._get_vendedor,
            'get_address_partner': self._get_address_partner,
            'set_totales': self._set_totales,
            'get_invoices': self._get_invoices,
            'get_total': self._get_total,
            'get_cant': self._get_cant,
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today
        
    def _get_vendedor(self,zona):
        vendedor = ''
        sql = """
        SELECT name 
        FROM	res_partner 
        WHERE active=True AND salesman=True AND code_zone_id=%d ;
        """%zona
        self.cr.execute (sql)
        result = self.cr.fetchall()
        if result:
            vendedor = result[0][0]	 	
        return vendedor

    def _get_invoices(self,promo):
        address_delivery = []
        facts = 'SF'
        sql = """
        SELECT i.name 
        FROM         sale_promocion_invoice_line AS l
        INNER  JOIN  account_invoice             AS i ON l.invoice_id=i.id  
        WHERE  promocion_id=%d ;"""%promo
        self.cr.execute (sql)
        result = self.cr.fetchall()
        if result:
            facts = ''
            for l in result:
                facts += '  ' + l[0]	 	
        return facts 

    def _get_address_partner(self,partner):
        address_delivery = []
        sql = """
        SELECT a.street,a.street2,a.phone,s.name,c.name
        FROM	      res_partner_address     AS a 
        INNER  JOIN   res_country_state       AS s ON a.state_id=s.id 
        INNER  JOIN   res_state_city          AS c ON a.city_id=c.id 
        WHERE a.type='default' AND a.partner_id=%d ;"""%partner
        self.cr.execute (sql)
        result = self.cr.fetchall()
        if result:
            address_delivery = result[0]	 	
        return address_delivery 

    def _set_totales(self,promo):
        self.cant = 0
        self.total= 0
        sql = """
        SELECT SUM(quantity) AS cantidad, SUM(price) AS total
        FROM	sale_promocion_line  
        WHERE promocion_id=%d;
        """%promo
        self.cr.execute (sql)
        result = self.cr.fetchall()
        if result:
            self.cant  = result[0][0]
            self.total = result[0][1]
        return

    def _get_total(self):
        return self.total

    def _get_cant(self):
        return self.cant

report_sxw.report_sxw('report.sale_promocion','sale.promocion','addons/custom_american/promociones/report/report_promocion_ventas.rml',parser=promo, header=False)