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

class comiss_invoice_zone(report_sxw.rml_parse):
    #Variables Globales----------------------------------------------------
    currentId	= 0
    totalcajas	= 0
    value_total = 0

    def __init__(self, cr, uid, name, context):
		super(comiss_invoice_zone, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'set_parameters': self._set_parameters,
			'set_init': self._set_init,
			'get_value_total': self._get_value_total,
			'set_total_cajas': self._set_total_cajas,
			'get_total_cajas': self._get_total_cajas,
			'get_mes': self._get_mes,
			'get_year': self._get_year,
		})
    def _set_init(self):
        self.totalcajas = 0
        return

    def _set_parameters(self,zone_id):
        self.value_total = 0
        parameter_id = pooler.get_pool(self.cr.dbname).get('parameters.seller.zone').search(self.cr, self.uid, [('zone_id','=',zone_id) ])
        parameters	 = pooler.get_pool(self.cr.dbname).get('parameters.seller.zone').read(self.cr, self.uid,  parameter_id,['value_total'])        
        if parameters:
            self.value_total = parameters[0]['value_total']
        return

    def _get_value_total(self):
        return self.value_total
    
    def _set_total_cajas(self,cajas):
        self.totalcajas += cajas
        return
    
    def _get_total_cajas(self):
        return self.totalcajas

    def _get_mes(self,code):
        meses	= (['01','ENERO'],['02','FEBRERO'],['03','MARZO'],['04','ABRIL'],['05','MAYO'],['06','JUNIO'],['07','JULIO'],['08','AGOSTO'],['09','SEPTIEMBRE'],['10','OCTUBRE'],['11','NOVIEMBRE'],['12','DICIEMBRE'])
        mp = ''
        mes = ''
        if code:
            mp = code.strip()
        for m in meses:
            if m[0] == mp:
                mes	= m[1]
        return mes

    def _get_year(self,fecha):
        year  = ''
        if fecha:
            year  = fecha[0:4]
        return year

report_sxw.report_sxw('report.commissions_invoice_zone','commissions.seller','addons/custom_american/custom_sale/report/report_commissions_seller_invoice_zone.rml',parser=comiss_invoice_zone, header=False)
