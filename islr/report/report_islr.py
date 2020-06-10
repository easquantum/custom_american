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

class islr(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(islr, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale, 
            'get_tipo': self._get_tipo,
            'get_today': self._get_today,
            'get_address_company':self._get_address_company,
            'get_address_partner':self._get_address_partner,
            'get_razon_partner':self._get_razon_partner,
            'get_invoice': self._get_invoice,			
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today


    def _get_invoice(self,islr_id):
        nrfact = 'N/A'
        obj_islr = pooler.get_pool(self.cr.dbname).get('account.islr.tax')
        islr     = obj_islr.browse(self.cr, self.uid, islr_id)
        if islr.islr_line:
            nrfact = islr.islr_line[0].invoice_id.number_document
        return nrfact

    def _get_tipo(self,type):
        tipo = ''
        if type and type == 'legal':
            tipo = 'Juridico'
        else:
            tipo = 'Natural'
        return tipo

    def _get_address_company(self,company): 
        sql="""
        SELECT d.street,d.street2, d.phone 
        FROM res_company AS c 
        INNER JOIN res_partner AS p ON  c.partner_id=p.id 
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE c.id=%d;"""%company
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dir = datos[0][0] + "  " + datos[0][1] + "    Telf: " + datos[0][2]
        return dir

    def _get_address_partner(self,partner): 
        sql="""
        SELECT d.street,d.street2, d.phone 
        FROM  res_partner AS p  
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE p.id=%d AND d.type='default';"""%partner
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dir = datos[0][0] + "  " + datos[0][1] + "    Telf: " + datos[0][2]
        return dir

    def _get_razon_partner(self,partner): 
        sql="""
        SELECT d.name 
        FROM  res_partner AS p  
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE p.id=%d AND d.type='default';"""%partner
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dir = datos[0][0]
        return dir
        
report_sxw.report_sxw('report.islr','account.islr.tax','addons/custom_american/islr/report/report_islr.rml',parser=islr, header=False)
