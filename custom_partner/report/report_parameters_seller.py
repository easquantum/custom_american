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

class parameters_seller(report_sxw.rml_parse):
    totalgral  = 0
    cont       = 0
    currentId	= 0
    def __init__(self, cr, uid, name, context):
        super(parameters_seller, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'set_total': self._set_total, 
            'get_total': self._get_total,
            'get_today': self._get_today,
            'get_item': self._get_item,			
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today

    def _get_item(self):
        self.cont += 1
        return self.cont
        
    def _set_total(self,monto,seller):
        if self.currentId == 0 or self.currentId != seller:
            self.totalgral  = 0
            self.currentId = seller
        self.totalgral  += monto
        return 

    def _get_total(self):
        return self.totalgral

report_sxw.report_sxw('report.parameters','res.partner','addons/custom_american/custom_partner/report/report_parameters_seller.rml',parser=parameters_seller, header=False)
