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


class comisiones_cobranza(report_sxw.rml_parse):
    #Variables Globales----------------------------------------------------
    currentId	= 0
    total	= 0

    def __init__(self, cr, uid, name, context):
		super(comisiones_cobranza, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'get_total': self._get_total,
			'get_mes': self._get_mes,
			'get_client': self._get_client,
		})
       
    def _get_total(self):
        return self.total

    def _get_client(self,ro):
        cliente = ''
        sql= """
        SELECT  rp.name
        FROM account_payment_method AS pm
        INNER JOIN res_partner AS rp ON pm.partner_id=rp.id
        WHERE control_number='%s'
        """%ro
        self.cr.execute (sql)
        resultSQL = self.cr.fetchall()
        if resultSQL and resultSQL[0]:
            cliente = resultSQL[0][0]
        return cliente

    def _get_mes(self,fecha):
        meses	= (['01','ENERO'],['02','FEBRERO'],['03','MARZO'],['04','ABRIL'],['05','MAYO'],['06','JUNIO'],['07','JULIO'],['08','AGOSTO'],['09','SEPTIEMBRE'],['10','OCTUBRE'],['11','NOVIEMBRE'],['12','DICIEMBRE'])
        mp = fecha[5:7]
        mes = ''
        for m in meses:
            if m[0] == mp:
                mes	= m[1]
        return mes
report_sxw.report_sxw('report.commissions_collection','commissions.collection.seller','addons/custom_american/custom_sale/report/report_commissions_collection_seller.rml',parser=comisiones_cobranza, header=False)
