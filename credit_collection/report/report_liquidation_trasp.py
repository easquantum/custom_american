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

class liquidation_tras(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	totalflete		= 0
	totalcajas		= 0
	tarifas      	= []
	def __init__(self, cr, uid, name, context):
		super(liquidation_tras, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_today': self._get_today,
			'get_invoices': self._get_invoices,
			'get_product_line': self._get_product_line,
			'get_totalcajas': self._get_totalcajas,
			'get_totalflete': self._get_totalflete,
			'get_totalpagar': self._get_totalpagar,				
		})

	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today
		
	def _get_invoices(self,guide):
		sql = """
		SELECT  p.name,w.name,SUM(m.product_qty) AS cajas   
		FROM	delivery_guide_picking_line    	 AS l
		INNER  JOIN stock_picking    	         AS p	 ON l.picking_id=p.id
		INNER  JOIN stock_move                   AS m	 ON p.id=m.picking_id
		INNER  JOIN stock_warehouse              AS w	 ON p.warehouse_dest_id=w.id 
		WHERE l.guide_id=%d
		GROUP BY p.name,w.name ;"""%guide
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"traspaso":'',"destino":'',"cajas":0}]
			
		resp = []
		self.totalcajas = 0 
		for trasp in resultSQL:
			tnro		= trasp[0]
			destino		= trasp[1]
			cantidad	= trasp[2]
			self.totalcajas += cantidad
			resp.append({"traspaso":tnro,"destino":destino,"cajas":cantidad})
		return resp
		
	def _get_product_line(self,liquid,guide):
		self.totalflete = 0
		self.totalcajas = 0	
		self.tarifas 	= []		
		sqlg = """	
		SELECT  id_flete,price,name 
		FROM liquidation_shipping_line_fl  
		WHERE liquidation_ids=%d ;"""%(liquid) 
		self.cr.execute (sqlg)		
		self.tarifas = self.cr.fetchall()	
		sqlp = """	
		SELECT SUM(s.product_qty) as cantidad,p.id_flete 
		FROM delivery_guide_picking_line AS l  
		INNER JOIN stock_move AS s ON l.picking_id=s.picking_id 
		INNER JOIN product_product AS p ON s.product_id=p.id 
		WHERE l.guide_id=%d 
		GROUP BY p.id_flete  ;"""%guide	 						
		self.cr.execute (sqlp)
		resultSQLP = self.cr.fetchall()
		
		resptar = []
		for product in resultSQLP:
			costo	= 0
			total   = 0
			cant	= product[0]
			vtarifa	= ''
			self.totalcajas += product[0]
			for tarf in self.tarifas:				
				if tarf[0] == product[1]:
					costo 	= tarf[1] 
					total 	= cant * costo
					vtarifa = tarf[2] + ':   ' + str(costo)
					self.totalflete += total
					break	
			resptar.append({"cajas":cant,"tarifa":vtarifa,"total":total}) 
			#self.totalcajas += inf[4]
		return resptar

	def _get_totalcajas(self):
		return self.totalcajas	

	def _get_totalflete(self):
		return self.totalflete

	def _get_totalpagar(self):
		totalpagar = self.totalflete - self.dtotalflete
		return totalpagar
										
report_sxw.report_sxw('report.liquidation_shipping_trasp','liquidation.shipping','addons/custom_american/credit_collection/report/report_liquidation_trasp.rml',parser=liquidation_tras, header=False)
