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

class comprobante_contable(report_sxw.rml_parse): 
    ttdebe  = 0
    tthaber = 0    
                
    def __init__(self, cr, uid, name, context):
        super(comprobante_contable, self).__init__(cr, uid, name, context)        
        self.localcontext.update({
            'time': time,
			'locale': locale,
            'set_total': self._set_total,
            'get_compro': self._get_compro,
            'get_debe': self._get_debe,
            'get_haber': self._get_haber,
        })
   
        
    def _set_total(self,debe,haber):
        self.ttdebe += debe
        self.tthaber += haber
        return     

    def _get_debe(self):
            return self.ttdebe

    def _get_haber(self):
            return self.tthaber

    def _get_compro(self,ids):
        comp = ''
        self.ttdebe = 0
        self.tthaber = 0
        lines_id = pooler.get_pool(self.cr.dbname).get('account.move.line').search(self.cr, self.uid, [('move_id','=',ids)])
        mov = pooler.get_pool(self.cr.dbname).get('account.move.line').read(self.cr, self.uid, lines_id,['ref'])
        if mov and mov[0]:
           comp = mov[0]['ref'] 
        return comp
    

report_sxw.report_sxw('report.comprobante_contable','account.move','addons/custom_american/custom_account/report/report_comprobante_contable.rml',parser=comprobante_contable, header=False)
