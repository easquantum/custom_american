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

class wizard_islr(report_sxw.rml_parse):
    islr_data = False
    company_name = ''
    company_rif  = ''
    company_id   = 0
    partner_id   = 0
    document_date  = ''
    document_number  = ''
    amount_base      = 0
    amount_islr = 0
    tax_islr = 0
    code = 0
    islr_name  = ''
    def __init__(self, cr, uid, name, context):
        super(wizard_islr, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_today': self._get_today,
            'get_number': self._get_number,
            'get_company':self._get_company,
            'get_company_rif':self._get_company_rif,
            'get_address_company':self._get_address_company,
            'get_razon_partner':self._get_razon_partner,
            'get_partner_rif':self._get_partner_rif,
            'get_address_partner':self._get_address_partner,
            'get_date': self._get_date,
            'get_invoice': self._get_invoice,
            'get_base': self._get_base,
            'get_amount_islr': self._get_amount_islr,
            'get_tax': self._get_tax,
            'get_code': self._get_code,
            'get_islr_name': self._get_islr_name,
            })

    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today

    def _get_base(self):
        return self.amount_base

    def _get_amount_islr(self):
        return self.amount_islr

    def _get_tax(self):
        return self.tax_islr

    def _get_code(self):
        return self.code

    def _get_islr_name(self):
        return self.islr_name

    def _get_number(self,data):
        invoice_id = data['id']
        invoice 	= pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr,self.uid, [invoice_id],['islr_number','number_document'])[0]
        islr_id	  = pooler.get_pool(self.cr.dbname).get('account.islr.tax').search(self.cr, self.uid, [('name','=',invoice['islr_number']) ]) 
        obj_islr  = pooler.get_pool(self.cr.dbname).get('account.islr.tax')
        islr_data = obj_islr.browse(self.cr, self.uid, islr_id[0])
        number_comp = invoice['islr_number']
        self.document_number = invoice['number_document']
        self.company_id   = islr_data.company_id.id
        self.company_name = islr_data.company_id.name
        self.company_rif  = islr_data.company_id.partner_id.vat
        self.partner_id   = islr_data.partner_id.id
        self.partner_rif  = islr_data.partner_id.vat
        self.document_date  = islr_data.document_date
        self.amount_base   = islr_data.base
        self.amount_islr   = islr_data.amount_islr
        self.tax_islr      = islr_data.porcentaje
        self.code         = islr_data.islr_type_id.code
        self.islr_name    = islr_data.islr_type_id.name
        return number_comp

    def _get_tipo(self,type):
        tipo = ''
        if type and type == 'legal':
            tipo = 'Juridico'
        else:
            tipo = 'Natural'
        return tipo

    def _get_company(self):
        return self.company_name

    def _get_company_rif(self):
        return self.company_rif

    def _get_address_company(self): 
        sql="""
        SELECT d.street,d.street2, d.phone 
        FROM res_company AS c 
        INNER JOIN res_partner AS p ON  c.partner_id=p.id 
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE c.id=%d;"""%self.company_id
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dir = datos[0][0] + "  " + datos[0][1] + "    Telf: " + datos[0][2]
        return dir

    def _get_razon_partner(self): 
        razon_social = ''
        sql="""
        SELECT d.name 
        FROM  res_partner AS p  
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE p.id=%d AND d.type='default';"""%self.partner_id
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        if datos and datos[0]:
            razon_social = datos[0][0]
        return razon_social

    def _get_partner_rif(self):
        return self.partner_rif

    def _get_address_partner(self): 
        sql="""
        SELECT d.street,d.street2, d.phone 
        FROM  res_partner AS p  
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE p.id=%d AND d.type='default';"""%self.partner_id
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dirp = datos[0][0] + "  " + datos[0][1] + "    Telf: " + datos[0][2]
        return dirp

    def _get_date(self):
        return self.document_date

    def _get_invoice(self):
        return self.document_number

report_sxw.report_sxw('report.wizard_islr','account.islr.tax','addons/custom_american/islr/report/report_wizard_islr.rml',parser=wizard_islr, header=False)
