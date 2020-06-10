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
import datetime
import locale
from report import report_sxw
from osv import osv
import pooler

class guide_traspaso(report_sxw.rml_parse):
    #Variables Globales----------------------------------------------------
    totalpeso = 0
    totalcajas = 0
    #----------------------------------------------------------------------
    def __init__(self, cr, uid, name, context):
        super(guide_traspaso, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale, 
            'get_today': self._get_today,
            'get_piking_line': self._get_piking_line,
            'get_totalcajas': self._get_totalcajas,
            'get_totalpeso': self._get_totalpeso
        })

    def _get_piking_line(self,guide_id):
        self.totalpeso = 0
        self.totalcajas = 0
        sqlp = """
            SELECT  p.default_code,t.name,p.variants,SUM(m.product_qty) AS cantidad,t.weight_net  
            FROM	delivery_guide_picking_line    	 AS d
            INNER  JOIN stock_move AS m	 ON d.picking_id=m.picking_id
            INNER  JOIN product_product 	 AS p	 ON m.product_id=p.id
            INNER  JOIN product_template 	 AS t	 ON p.product_tmpl_id=t.id
            WHERE d.guide_id=%d
            GROUP BY p.default_code,t.name,p.variants,t.weight_net ;"""%guide_id
        self.cr.execute (sqlp)
        resultSQL = self.cr.fetchall()
        if not resultSQL:
            return [{"codigo":'',"producto":'',"referencia":'',"cajas":0,"peso":0}]
        rsp = []
        for inf in resultSQL:
            peso = 0		
            if inf[4]: 
                peso += inf[3] * inf[4]
                self.totalpeso += peso	
            rsp.append({"codigo":inf[0],"producto":inf[1],"referencia":inf[2],"cajas":inf[3],"peso":peso}) 
            self.totalcajas += inf[3]
        return rsp

    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today

    def _get_totalcajas(self):
        return self.totalcajas	

    def _get_totalpeso(self):
        return self.totalpeso
						
report_sxw.report_sxw('report.delivery_guide_traspaso','delivery.guide','addons/custom_american/delivery_guide/report/report_guide_traspaso.rml',parser=guide_traspaso, header=False)
