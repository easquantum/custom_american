# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Corvus Latinoamerica, C.A. 
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

class declaracion_iva_compras(report_sxw.rml_parse):
	#Variables Globales----------------------------------------------------
	ttcompra	= 0
	ttretencion	= 0
	ttbase		= 0
	ttiva		= 0
	ttexento	= 0	
	#--------------------------------------------------------------------------
	def __init__(self, cr, uid, name, context):
		super(declaracion_iva_compras, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'locale': locale,
			'procesar_datos': self._procesar_datos,
			'crear_archivo': self._crear_archivo,
			'get_iva_seniat': self._get_iva_seniat,
			'get_comprobante_retenc': self._get_comprobante_retenc,
			'get_totalgral_compra': self._get_totalgral_compra,
			'get_totalgral_base': self._get_totalgral_base,
			'get_totalgral_exento': self._get_totalgral_exento,
			'get_totalgral_ivaretenido': self._get_totalgral_ivaretenido,
			'get_company':self._get_company,
			'get_periodo': self._get_periodo,
		})
	
	def _procesar_datos(self,listado,fecha):
		#inicializacion de variables--------------------------------------------------------------------------------------------------------------------------------------
		datosiva		= []
		cont			= 0
		for invoices in listado:
			#Inicializacion Variables Locales-----------------------------------------------------------------------------------------------------------------------------
			base		= 0
			iva			= 0
			ivaret		= 0
			totoal		= 0
			exento		= 0 
			alicuota	= 0	
			totalsin	= 0
			ret			= 0
			tipodoc		= '01'          # Tipo Documento [01:Compra 02:  03:Nota de Credito 04:]
			nrofa		= ''            # Nro. Factura Afectada
			invoiceid	= invoices[0]	# ID de la Factura
			finvoice	= invoices[1]	# Fecha en que el Proveedor Emitio la Factura
			nrofact		= invoices[2]	# Nro Factura del Proveedor
			nrocont		= invoices[3]	# Nro de Control de la Factura Proveedor
			amounttax	= invoices[4]	# Total Impuestos y/o descuentos
			amountotal	= invoices[5]	# Total Factura + Impuestos - Descuentos			
			partnerid	= invoices[6]	# ID del Proveedor
			rifprov		= invoices[7]	# RIF del Proveedor 
			porcret		= invoices[8]   # Procentaje de Retencion del Proveedor
			codprov		= invoices[9]	# Codigo Proveedor
			razonsocial	= invoices[10]	# Nombre del Proveedor
			nrocomprob	= invoices[11]  #Comprobnte de Retencion
			tipo		= invoices[12]       # Tipo Documento [Compra,Nota Credito] 
			#nrocomprob	= self._get_comprobante_retenc(codprov,fecha) #Comprobnte de Retencion

			#Se obtiene la Razon Social del cliente: ---------------------------------------------------------------------------------
			#Esta debe corresponder a la direccion por defecto de la tabla res_partner_address
			address_id	= pooler.get_pool(self.cr.dbname).get('res.partner.address').search(self.cr, self.uid, [('partner_id','=',partnerid),('type','=','default')])
			address_dat = pooler.get_pool(self.cr.dbname).get('res.partner.address').read(self.cr,self.uid, address_id,['name'])
			if address_dat and address_dat[0]['name']:
				razonsocial = address_dat[0]['name']

			#Se consultan los Impuesto y/o descuentos ----------------------------------------------------------------------------------------------
			tax_ids 	= pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoiceid) ])
			result_tax 	= pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr,self.uid, tax_ids,['name', 'base','amount'])
			if result_tax:
				#Productos EXENTOS-----------------------------------------------------------------------------------------------
				#Se valida si posee productos exentos de impuesto
				sqlsin="""
							SELECT SUM(a.price_unit * a.quantity) AS total  
							FROM account_invoice_line AS a 
							WHERE invoice_id=%d  AND a.id 
							NOT IN (SELECT t.invoice_line_id  FROM  account_invoice_line_tax AS t 	WHERE a.id = t.invoice_line_id);"""%invoiceid
				self.cr.execute (sqlsin)
				rslt = self.cr.fetchall()
				if rslt and rslt[0][0]:
					exento			=  rslt[0][0]
					self.ttexento	+= exento
				#Se descartan los descuentos y otros impuestos diferente del tipo 'vat' o  IVA  
				for tax in result_tax:
					#Se consulta el Grupo o tipo de Tax-----------------------------------------------------------------------------------------
					#los impuestos correspondientes al IVA, deben pertenecer al tipo 'vat'
					#para poder ser procesados correctamente, de lo contraio seran descartados
					tax_id		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
					tax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])
					#Procesar FACTURAS CON  IMPUESTOS-------------------------------------------------------------------------------------------					
					if tax_info[0]['tax_group'] == 'vat':
						alicuota	= tax_info[0]['amount'] * 100
						iva			= tax['amount']
						base		= tax['base']
						total		= base + iva + exento
						ivaret      = 0
						if iva and porcret > 0:
							ivaret = iva * porcret / 100
							
						#Totales--------------------------------------------------------------------------------
						if tipo == 'in_invoice' or tipo == 'in_invoice_ad':
						    self.ttbase		+= base
						    self.ttiva		+= iva
						    self.ttretencion	+= ivaret
						    self.ttcompra	+= total
						else:
						    tipodoc = '03'
						    nota = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, [invoiceid],['parent_id'])
						    if nota and nota[0]['parent_id']:
						        f_id = nota[0]['parent_id'][0]
						        fact = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, [f_id],['number_document'])
						        if fact and fact[0]['number_document']:
						            nrofa = fact[0]['number_document']
						    self.ttbase		-= base
						    self.ttiva		-= iva
						    self.ttretencion	-= ivaret
						    self.ttcompra	-= total
						cont += 1
						datosiva.append({'cont':cont,'fecha':finvoice,'rif':rifprov,'proveedor':razonsocial,'tipo_op':'C','tipo_doc':tipodoc,'nrofac':nrofact,'nrocont':nrocont,'afect':nrofa,'total':total,'exento':exento,'base':base,'alicuota':alicuota,'iva':ivaret,"nrocomprobante":nrocomprob}) 
		return datosiva
		
	def _crear_archivo(self,datosivaseniat,fecha):
		#Creando  Archivo Plano del SENIAT--------------------------------------------------------------------------------------------------------
		#
		#Ruta del archivo-----------------------------------------------------------------------------------------------
		ruta		= "/home/public/" # Desarrollo
		ruta		= "/opt/openerp/reportes/compras/" # Servidor de Produccion

		#Nombre del archivo--------------------------------------------------------------------------------------------------------------------------------------------------------------
		meses	= (['01','ENE'],['02','FEB'],['03','MAR'],['04','ABR'],['05','MAY'],['06','JUN'],['07','JUL'],['08','AGO'],['09','SEP'],['10','OCT'],['11','NOV'],['12','DIC'])
		p 		= '-1'  
		a		= fecha[:4]
		m		= fecha[5:7]
		m		= str(m) 
		d		= fecha.split('-')
		for x in meses:
			if x[0] == m:
				m	= x[1]
		if int(d[2]) > 15:
			p = '-2'
		nb		= m+a+p+".txt"
		filename	= ruta+nb			
		output	= open(filename,"w")
		 
		#Variables del archivo para el seniat-----------------------------------------------------------------------------------
		ff	= ''							#Fecha Factura
		rp	= '0000000000' 					#Rif Proveedor
		nf	= '0'							#Nro Factura
		nc	= '0'							#Nro Control
		fa	= '0'							#Nro Factura Afectada
		tp	= '0'							#Tipo Documento
		nr	= ''							#Nro Comprobante Retencion
		rc	= self._get_company()[1]		#rif empresa
		pr	= fecha[:4]+fecha[5:7]			#Periodo de la Declaracion
		tc	= '0.0'						#Total Compra
		bs	= '0.0'						#Monto Base
		ir	= '0.0'						#Iva Retenido
		al	= '0.0'						#Alicuota
		ex	= '0.0'						#Monto Exento

						
		for datos in datosivaseniat:
			#Asignando Datos 
			if  datos['fecha']:
				ff	= datos['fecha']
			if datos['rif']:
				rp	= datos['rif']
			if datos['nrofac']:
				nf	= datos['nrofac']
			if datos['nrocont']:
				nc	= datos['nrocont']	
			
			nr	= datos['nrocomprobante']
			tp	= datos['tipo_doc']
			tc	= '0.0'	
			bs	= '0.0'
			ir	= '0.0'	
			ex	= '0.0'
			fa	= '0'					
			if datos['afect']:
				fa	= datos['afect'] 
			if  datos['total'] > 0:
				tc	=	locale.format('%.2f',  datos['total'], grouping=True)
				tc	=	tc.replace(',','.')
			if 	datos['base'] > 0:
				bs	=	locale.format('%.2f',  datos['base'], grouping=True)
				bs	=	bs.replace(',','.')										
			if 	datos['iva'] > 0:
				ir	=	locale.format('%.2f',  datos['iva'], grouping=True)
				ir	=	ir.replace(',','.')							
			if 	datos['exento'] > 0:
				ex	=	locale.format('%.2f',  datos['exento'], grouping=True)
				ex	=	ex.replace(',','.')	
			if 	datos['alicuota'] > 0:
				al	=	locale.format('%.2f',  datos['alicuota'], grouping=True)
				al	=	al.replace(',','.')								
			#print  "REG",rc,pr,ff,'C',tp,rp,nf,nc,tc,bs,ir,fa,nr,ex,al 
			reg = rc+"	"+pr+"	"+ff+"	"+'C'+"	"+tp+"	"+rp+"	"+nf+"	"+nc+"	"+tc+"	"+bs+ "	"+ir+"		"+fa+"	"+nr+"	"+ex+"	"+al+"	0\t\n" 
			#print reg 				
			output.write(reg)
		#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
		output.close() 
		return	

	def _get_iva_seniat(self, form):
		#inicializacion de variables Globale------------------------------------------------------------------------------------------
		self.ttcompra		= 0
		self.ttretencion	= 0
		self.ttbase			= 0
		self.ttiva			= 0
		self.ttexento		= 0
		
		#inicializacion de variables Locales------------------------------------------------------------------------------------------		
		ivaseniat	= []
		fdesde		= form['date1']
		fhasta		= form['date2']	
		create_file	= form['crear']
		orderby		= 'p.name'
		filtro		= "'in_refund','"+form['filtro']+"'"
		if create_file:
		    orderby		= 'a.date_document'
		if form['filtro'] == 'todo':
			filtro = "'in_invoice','in_invoice_ad','in_refund'"
		#Datos FACTURAS COMPRAS	
		sql = """
		SELECT  a.id, a.date_document, a.number_document, a.number_control, a.amount_tax, a.amount_total, p.id, p.vat, a.p_ret, p.ref, p.name, a.number_retention, a.type    
		FROM 	  account_invoice AS a 
		INNER JOIN res_partner AS p ON a.partner_id=p.id 
		WHERE  a.type in (%s)  AND a.state!='cancel' AND a.retention=True AND a.date_invoice BETWEEN '%s' AND '%s'  
		ORDER BY %s;"""%(filtro,fdesde,fhasta,orderby)	
		#print sql
		self.cr.execute (sql)
		listado = self.cr.fetchall()
		if not listado:
			return [{'cont':'','fecha':'','rif':'','proveedor':'','tipo_op':'','tipo_doc':'','nrofac':'','nrocont':'','afect':'','total':0,'exento':0,'base':0,'alicuota':0,'iva':0,"nrocomprobante":0}]			
		ivaseniat = self._procesar_datos(listado,fdesde)

		#Funcion para Crear Archivo		
		if create_file and ivaseniat: 
			x = self._crear_archivo(ivaseniat,fhasta)

		return ivaseniat

	def _get_totalgral_compra(self): 
		return self.ttcompra

	def _get_totalgral_base(self): 
		return self.ttbase
		
	def _get_totalgral_ivaretenido(self): 
		return self.ttretencion

	def _get_totalgral_exento(self): 
		return self.ttexento
		
	def _get_company(self):
		sql = " SELECT c.name,p.vat FROM res_company AS c  INNER JOIN res_partner AS p ON  c.partner_id=p.id;" 
		self.cr.execute (sql)
		datos = self.cr.fetchall()
		company = datos[0]
		return company

	def _get_comprobante_retenc(self,codigo,fecha):
		f= fecha.split('-')
		codpartner = codigo.zfill(8) 
		numero_comp = f[0]+f[1]+codpartner
		return numero_comp

	def _get_periodo(self,fecha):
		f= fecha.split('-')
		if int(f[2]) < 15:
			quincena = '  Primera Quincena'
		else:
			quincena = '  Segunda Quincena'
		periodo = f[1] + ' - ' + f[0] + quincena	
		return periodo

report_sxw.report_sxw('report.declaracion_ivaco_seniat','account.invoice','addons/custom_american/custom_account/report/declaracion_ivaco_seniat.rml',parser=declaracion_iva_compras, header=False)
