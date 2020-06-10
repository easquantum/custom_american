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

class liquidation_m(report_sxw.rml_parse):
	totalflete		= 0
	totalcajas		= 0
	dtotalflete	= 0
	dtotalcajas	= 0
	tarifas      	= []
	def __init__(self, cr, uid, name, context):
		super(liquidation_m, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_today': self._get_today,			
		})

	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today		
													
report_sxw.report_sxw('report.liquidation_manual','liquidation.shipping','addons/custom_american/credit_collection/report/report_liquidation_manual.rml',parser=liquidation_m, header=False)
