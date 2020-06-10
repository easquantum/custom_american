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

class tarifas_alm(report_sxw.rml_parse):
	totalflete		= 0
	totalcajas		= 0
	dtotalflete	= 0
	dtotalcajas	= 0
	tarifas      	= []
	def __init__(self, cr, uid, name, context):
		super(tarifas_alm, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale, 
			'get_today': self._get_today,
			'get_warehouse': self._get_warehouse,
			'get_tarifas': self._get_tarifas, 
		})

	def _get_today(self):
		today = datetime.datetime.now().strftime("%d/%m/%Y")
		return today		

	def _get_tarifas(self,form):
		#Inicializacion de variables Globales--------------------------------------------------------------------------------------		
		resp	= []
		almacen	= form['warehouse']
		ruta	= ''
		vehic	= ''
		mas			= 0
		otro		= 0
		#Consulta Compras del periodo-------------------------------------------------------------------------------------------------	
		sql = """
		SELECT  r.name,r.note,t.name,p.name,l.price   
		FROM   guide_ruta AS r 
		INNER  JOIN guide_ruta_line AS l ON r.id=l.ruta_id
		INNER  JOIN guide_tipo_vehiculo AS t ON l.tipo_vehiculo_id=t.id
		INNER  JOIN product_category_fle AS p ON l.category_fle_id=p.id
		WHERE  r.warehouse_id=%d 
		ORDER BY r.name,t.name,p.name;"""%(almacen)
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return [{"ruta":'',"descrip":'',"vehiculo": '',"mas": 0,"otro": 0}]

		for tarifas in resultSQL:
			nomruta 	= tarifas[0]
			notas		= tarifas[1]
			vehiculo	= tarifas[2]
			catg		= tarifas[3]
			precio		= tarifas[4]
			catg		= catg.upper()
			if vehic != vehiculo:
				vehic	= vehiculo				
				if catg.rfind('MAS') >= 0:
					mas = precio
				else:
					otro = precio
			else:
				if ruta != nomruta:
					ruta = nomruta
				else:
					nomruta	= ''
					notas	= '' 
				if catg.rfind('MAS') >= 0:
					mas = precio
				else:
					otro = precio
				resp.append({"ruta":nomruta,"descrip":notas,"vehiculo": vehiculo,"mas":mas,"otro":otro})
				mas		= 0
				otro	= 0
		return resp

	def _get_warehouse(self,warehouse):
		almacen = ''
		sql = "SELECT name FROM stock_warehouse	WHERE id=%d;"%warehouse
		self.cr.execute (sql)
		resultSQL = self.cr.fetchall()
		if resultSQL and resultSQL[0]: 
			almacen = resultSQL[0][0]
		return almacen

report_sxw.report_sxw('report.ruta_tarifas','guide.ruta','addons/custom_american/delivery_guide/report/tarifas_almacen.rml',parser=tarifas_alm, header=False)
