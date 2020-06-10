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
import locale
from report import report_sxw
from osv import osv
import pooler

class ventas_netas_nac(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	totalcajas	= 0
	totalventas	= 0
	totaldscto	= 0
	totalgral	= 0
	#locale.setlocale(locale.LC_ALL,'es_VE.utf8')	
	#---------------------------------------------------------------------

	def __init__(self, cr, uid, name, context):
		super(ventas_netas_nac, self).__init__(cr, uid, name, context) 
		self.localcontext.update({
			'time': time, 
			'locale': locale,  
			'get_detalle': self._get_detalle, 
			'get_totalcajas': self._get_totalcajas,
			'get_totalventas': self._get_totalventas,
			'get_totaldscto': self._get_totaldscto,
			'get_totalgral': self._get_totalgral,			
			'get_user_owner': self._get_user_owner,						
		})

	def _get_detalle(self, form):		
		#Inicializacion Variables--------------------------------------------------------------------------------------------
		self.totalcajas		= 0
		self.totalventas	= 0
		self.totaldscto		= 0
		self.totalgral		= 0	
		fdesde				= form['date1']
		fhasta				= form['date2']
		product_act			= 0
		prov_act			= 0
		dscto_act			= 0
		cont				= 0
		tcajas				= 0
		totdscto			= 0
		tmp					= {}
		subcaja		= 0
		subventa	= 0
		subdscto	= 0
		subtotal	= 0		
		#Consulta  de las facturas correspondientes al periodo---------------------------------------------------------------					
		sql = """
		SELECT d.product_id,r.id,r.name,p.default_code,t.name,p.variants,sum(d.quantity),t.list_price,i.amount  
		FROM		account_invoice				AS a
		INNER JOIN	account_invoice_line		AS d ON a.id=d.invoice_id
		INNER JOIN 	product_product				AS p ON d.product_id=p.id
		INNER JOIN 	product_template			AS t ON p.product_tmpl_id=t.id
		INNER JOIN 	product_supplierinfo	 	AS s ON p.id=s.product_id
		INNER JOIN 	res_partner		 			AS r ON s.name=r.id		
		LEFT  JOIN	account_invoice_line_tax	AS x ON d.id=x.invoice_line_id 
		LEFT  JOIN	account_tax					AS i ON x.tax_id=i.id 		
		WHERE		a.state!='cancel' AND a.type='out_invoice' AND i.tax_group!='vat' AND a.date_invoice BETWEEN '%s' AND '%s' 
		GROUP BY d.product_id,r.id,r.name,p.default_code,t.name,p.variants,t.list_price,i.amount  
		ORDER BY r.name,p.default_code;"""%(fdesde,fhasta)
		#print sql
		self.cr.execute(sql)
		resultSQL = self.cr.fetchall()
		if not resultSQL:
			return []
		
		resp = [] 
		for products in resultSQL:
			product	= products[0]
			prov	= products[1]
			nombpv	= products[2]
			cod		= products[3]
			nombpd	= products[4]
			ref		= products[5]
			cajas	= products[6]
			precio	= products[7]
			dscto	= products[8]

			#Se valida si es el primer gegistro a procesar
			if cont == 0: 
				prov_act	= prov
				product_act	= product
				resp.append({"cod":'.-',"sp":'..', "nomb":nombpv,"ref":'',"cant":'',"precio":'',"venta":'',"descto":'',"total":''}) 
				tmp = {"cod":cod,"sp":'..........', "nomb":nombpd,"ref":ref,"cant":0,"precio":precio,"venta":0,"descto":0,"total":0}

			if prov_act != prov and product_act != product:
				subdscto	+= totdscto 
				subventa	+= venta	
				subtotal	+= tmp['total']		
				tcajas		= 0
				montodscto	= 0
				venta		= 0
				prov_act	= prov
				product_act	= product
				resp.append(tmp)
				resp.append({"cod":'',"sp":'', "nomb":'TOTAL =====>',"ref":'',"cant":subcaja,"precio":'',"venta":subventa,"descto":subdscto,"total":subtotal})
				resp.append({"cod":'',"sp":'SALTO DE LINEA......', "nomb":'',"ref":'',"cant":'',"precio":'',"venta":'',"descto":'',"total":''})
				resp.append({"cod":'.-',"sp":'..', "nomb":nombpv,"ref":'',"cant":'',"precio":'',"venta":'',"descto":'',"total":''})
				tmp = {"cod":cod,"sp":'..........', "nomb":nombpd,"ref":ref,"cant":0,"precio":precio,"venta":0,"descto":0,"total":0}
				#Acumula Totales Generales
				self.totalcajas 	+= subcaja
				self.totalventas	+= subventa
				self.totaldscto		+= subdscto
				self.totalgral		+= subtotal				
				#Se inicializan la Variebles
				subcaja		= 0
				subventa	= 0
				subdscto	= 0
				subtotal	= 0

			if prov_act == prov and product_act != product:
				subdscto	+= totdscto 
				subventa	+= venta
				subtotal	+= tmp['total']
				totdscto	= 0
				venta		= 0
				tcajas		= 0
				product_act	= product
				resp.append(tmp)
				tmp = {"cod":cod,"sp":'..........', "nomb":nombpd,"ref":ref,"cant":0,"precio":precio,"venta":0,"descto":0,"total":0}
			
			if prov_act == prov and product_act == product:
				tcajas			+= cajas
				subcaja			+= cajas
				venta 			= tcajas * precio
				tmp['cant']		= tcajas
				tmp['venta']	= venta 
				if dscto and dscto_act != dscto:
					dscto		= dscto * -1
					dscto_act	=  dscto
					montodscto	=  cajas * precio * dscto
					totdscto	+= montodscto
					tmp['descto']	= totdscto
					
				tmp['total'] = venta + totdscto
			cont				+= 1
		if tmp:
			#Acumula el ultimo registro procesado y se Totaliza 
			subdscto	+= totdscto 
			subventa	+= venta
			subtotal	+= tmp['total']
			#Acumula Totales Generales
			self.totalcajas 	+= subcaja
			self.totalventas	+= subventa
			self.totaldscto		+= subdscto
			self.totalgral		+= subtotal			
			resp.append(tmp)
			resp.append({"cod":'',"sp":'', "nomb":'TOTAL =====>',"ref":'',"cant":subcaja,"precio":'',"venta":subventa,"descto":subdscto,"total":subtotal})
		return resp		


	def _get_totalcajas(self):	
		return self.totalcajas

	def _get_totalventas(self):	
		return self.totalventas

	def _get_totaldscto(self):	
		return self.totaldscto

	def _get_totalgral(self):	
		return self.totalgral

	def _get_user_owner(self): 
		user	= pooler.get_pool(self.cr.dbname).get('res.users').read(self.cr, self.uid, [self.uid],['name'])								
		nombre	= user[0]['name']
		return nombre			
	
report_sxw.report_sxw('report.ventas_netas_nacional','account.invoice','addons/custom_american/custom_account/report/ventas_netas_nacional.rml',parser=ventas_netas_nac, header=False)
