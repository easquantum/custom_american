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
import commands
import wizard
import netsvc
import pooler
import codecs
from osv.orm import browse_record

#Formulario del Wizard - Datos Entrada
range_form = '''<?xml version="1.0"?>
<form string="Imprimir Nota Credito">
	<separator colspan="2" string="Indique los Datos"/>
	<newline/>
	<field name="printer"/>
	<field name="invoice"/>
</form>'''

TheFields = {
	'printer': {'string':'Impresora', 'type':'many2one','relation': 'ir.printers', 'required':True,  'size':90 },
	'invoice': {'string':'Nota Credito Nro.', 'type':'many2one','relation': 'account.invoice', 'required':True,  'size':90,  'domain':[('type','=','out_refund')] },
}


#Formulario del Wizard - Datos Salida
_result_form = '''<?xml version="1.0"?>
<form string="Informacion">
	<field name="resultado"/>
</form>''' 

_result_fields = {
	'resultado': {'string': 'Resultado','type': 'char','readonly': True, 'size':200},
} 


#Funcion para el formato de Cadenas de Caracteres
def _set_format_string(cadena,largo,alin):
	if not cadena:
	 	cadena = ''
	elif len(cadena) > largo:
		cadena	= cadena[:largo]
		
	if alin == 'ljust':
		cadena = cadena.ljust(largo)
	elif  alin == 'rjust':
		cadena = cadena.rjust(largo)
	elif  alin == 'center':
		cadena = cadena.center(largo)
	return cadena


def _invoice_print(self, cr, uid, data, context):
	#####Variables
	boldon	= chr(27)+chr(69)
	boldoff	= chr(27)+chr(70)	
	comprime	= chr(15)+chr(27)+'M'
	normal	= chr(18)+chr(27)+'P'
	saltopag	= chr(12)
	#ruta	= "/home/public/" # Ruta Desarrollo
	ruta	= "/opt/openerp/reportes/ventas/" # Ruta Server Produccion
	spacios_bnc = ''
	nrof	= ''.center(15)
	cliente	= ''.ljust(40)
	dir_ent1	= ''.ljust(40)
	zona		= ''.ljust(20)
	codcli	= ''.center(30)
	mes		= ''
	rsocial	= ''.ljust(60)
	dir_ent2	= ''.ljust(40)
	dir_fis1	= ''.ljust(58)
	dir_ent3	= ''.ljust(40)
	vendedor	= ''.ljust(35)	
	cpago	= ''.center(15)
	dir_fis2	= ''.ljust(60)
	cdad_ent	= ''.ljust(40)
	dir_fis3	= ''.ljust(60)
	edo_ent	= ''.ljust(40)
	fechap	= ''.ljust(20)
	nrop		= ''.ljust(20)
	fechaf	= ''
	loc_fis	= ''	
	tlf_ent	= ''.ljust(40)	
	tlf_fis	= ''.ljust(100)
	rifcli	= ''
	subtotal	= 0
	totalgral	= 0
	totaliva	= 0
	payment_id = 0
	monto_fact = 0
	totaldscto	= ''.rjust(10)
	if not data:
		return {'resultado':"No hay datos...!"}	
	#Consulta de datos generales de la Factura
	form = data['form']
	obj_invoice = pooler.get_pool(cr.dbname).get('account.invoice')	
	#Consulta Guia
	datosrefund = obj_invoice.browse(cr, uid, form['invoice'])

	if datosrefund:
		nrof		= _set_format_string(datosrefund.name,15,'center')			                    #Nro. Nota Credito
		f           =  datosrefund.date_invoice.split('-')
		fechaf      =  f[2] + '-'+ f[1] + '-' + f[0]
		mes			= _set_format_string('',4,'center')					                            #Mes Factura 
		nrop		= _set_format_string(datosrefund.reference,20,'ljust')		                    #Nro. Pedido
		fechaf		= _set_format_string(fechaf,20,'ljust')		                                    #Fecha Factura
		f           =  datosrefund.parent_id.date_invoice.split('-')
		fechap      =  f[2] + '-'+ f[1] + '-' + f[0]                                                #Fecha Pedido
		fechap		= _set_format_string(fechap,20,'ljust')		        
		codcli		= _set_format_string(datosrefund.partner_id.ref,27,'center')			        #Codigo del Cliente
		cliente		= _set_format_string(datosrefund.partner_id.name,40,'ljust')			        #Nombre del Cliente o Negocio
		rifcli		= _set_format_string(datosrefund.partner_id.vat,60,'ljust')			            #Rif Cliente
		zona		= _set_format_string(datosrefund.partner_id.code_zone_id.name,20,'ljust')		#Zona del Cliente
		rsocial		= _set_format_string(datosrefund.address_invoice_id.name,60,'ljust')			#Razon Social del Cliente
		tlf_fis		= _set_format_string(datosrefund.address_invoice_id.phone,60,'ljust')			#Telefono		
		dir_fis1	= _set_format_string(datosrefund.address_invoice_id.street,58,'ljust')			#Direccion Fiscal
		dir_fis3	= _set_format_string(datosrefund.address_invoice_id.street2,60,'ljust')			#
		cpago		= _set_format_string(datosrefund.payment_term.name,15,'center')		            #Condiciones de Pago
		notas_at	= _set_format_string(datosrefund.nota_atencion,30,'ljust')		                #Nota Manual
		payment_id	= datosrefund.payment_term.id					#ID Condiciones de Pago
		totalpagar	= ''.rjust(11)        #Total Pagar Documento
		monto_fact	= datosrefund.parent_id.amount_total        #Total  Factura
		if monto_fact:
		    monto_fact	= locale.format('%.2f',  monto_fact, grouping=True) 
		    monto_fact	= monto_fact.replace(',','.')
		    monto_fact	= monto_fact.ljust(20)
		else:
		    monto_fact	= _set_format_string('0.00',20,'ljust')
		nrog		= ''
		if datosrefund.parent_id.guide_id:
		    nrog		= datosrefund.parent_id.guide_id.name
		
		#Periodo Facturacion-------------------------------------------------------------------------
		pgp_obj = pooler.get_pool(cr.dbname).get('period.generalperiod')
		fch = datosrefund.parent_id.date_invoice
		pgp_ids = pooler.get_pool(cr.dbname).get('period.generalperiod').search(cr, uid, [('date_start','<=',fch),('date_stop', '>=',fch) ])
		if pgp_ids:
		    pg = pgp_obj.browse(cr, uid, pgp_ids)[0]
		    mes = _set_format_string(pg.code,6,'center')
		#Vendedor 
		#print "IDZONA",datosrefund.partner_id.code_zone_id.id
		if datosrefund.partner_id.code_zone_id.id:
		    vendedor_id		= pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',datosrefund.partner_id.code_zone_id.id),('salesman', '=', 1) ])
		    if vendedor_id:
		        nomb	= pooler.get_pool(cr.dbname).get('res.partner').read(cr, uid, vendedor_id,['name'])[0]['name']
		        vendedor = _set_format_string(nomb,40,'ljust') 

		#Validaciones tamaño del String
		if len(datosrefund.address_invoice_id.street) > 58:
		    dir_fis2	= datosrefund.address_invoice_id.street[58:120]
		    dir_fis2	= dir_fis2.ljust(60)		#
		if datosrefund.address_invoice_id.state_id:
			loc_fis	= datosrefund.address_invoice_id.state_id.name
		if datosrefund.address_invoice_id.city_id:
			loc_fis	+= ' '+datosrefund.address_invoice_id.city_id.name 
		
		loc_fis = _set_format_string(loc_fis,60,'ljust')
					
		##Datos de Direccion de Entrga
		##Consulta de datos entrega
		sqle = """
		SELECT d.street,d.street2,d.phone,s.name,c.name    
		FROM res_partner_address 	AS d
		LEFT JOIN res_country_state	AS s ON d.state_id=s.id 
		LEFT JOIN res_state_city		AS c ON d.city_id=c.id 
		WHERE partner_id=%d AND d.type='delivery';"""%datosrefund.partner_id.id
		cr.execute (sqle)
		reslt 	= cr.fetchall()
		if reslt:
			datos_e	= reslt[0] 		
			dir_ent1	= _set_format_string(datos_e[0],40,'ljust')
			dir_ent3	= _set_format_string(datos_e[1],40,'ljust')
			tlf_ent		= _set_format_string(datos_e[2],40,'ljust')
			edo_ent		= _set_format_string(datos_e[3],40,'ljust')
			cdad_ent	= _set_format_string(datos_e[4],40,'ljust')
			if datos_e[0] and len(datos_e[0]) > 40:
				dir_ent2	= _set_format_string(datos_e[0][41:81],40,'ljust')
	#Consulta de datos del Detalle
	sqlp = """
	SELECT d.id,p.default_code,s.product_code,t.name,p.variants,d.quantity,d.price_unit   
	FROM account_invoice_line		AS d
	INNER JOIN product_product		AS p ON d.product_id=p.id
	INNER JOIN product_template		AS t ON p.product_tmpl_id=t.id 
	LEFT JOIN  product_supplierinfo	AS s ON t.id=s.product_id
	WHERE d.invoice_id=%d;"""%datosrefund.id
	cr.execute (sqlp)
	result_d	= cr.fetchall()
	detalle	= []
	cdet	= 0
	ttcajas = 0
	if result_d:
		for inf in result_d:
			total	= 0
			iva	= 0
			descrip	= ''		
			if (inf[5] > 0) and (inf[6] > 0):
				total 	= inf[5]*inf[6]
				subtotal	+= total 
				importe	= locale.format('%.2f',  total, grouping=True)
				importe	= importe.replace(',','.')
			codigo	= inf[1].ljust(8)							#Codigo del Producto
			if inf[2]:											#Codigo Proveedor y Nombre del Producto
				descrip	= inf[2]
			if inf[3]:
				descrip	+= ' '+inf[3]							
			descrip	= _set_format_string(descrip,56,'ljust')							
			ref		= inf[4].center(10)							#Referencia
			cantidad	= locale.format('%.0f',  inf[5], grouping=True)	#Cantidad
			cantidad	= cantidad.replace(',','.')					#
			cantidad	= cantidad.center(4)						#
			precio	= locale.format('%.2f',  inf[6], grouping=True)	#
			precio	= precio.replace(',','.')					#Precio Unitario
			#precio	= precio.rjust(11)							#
			importe 	= importe.rjust(12)							#Total 
			ttcajas += inf[5]
			
			#Se consulta el valor del iva por producto
			sqli = """
			SELECT t.amount
			FROM account_invoice_line_tax AS r 
			INNER JOIN account_tax AS t ON r.tax_id=t.id
			WHERE r.invoice_line_id=%d AND t.tax_group='vat';"""%inf[0]
			cr.execute (sqli)
			result_i	= cr.fetchall() 
			if result_i:
				porc	= result_i[0][0]
				iva	= porc * 100
				iva	= locale.format('%.0f',  iva, grouping=True)
				iva	= iva.center(4)
				precio	= precio.rjust(11)		
			else:
				iva	= '0'.center(4)
				precio	+= ' (E)'
				precio	= precio.rjust(14)
				importe 	= importe.rjust(8)
			detline	= normal +codigo+ comprime+ descrip+ normal +ref+cantidad+precio+importe+iva+'\n'
			cdet		+= 1
			detalle.append(detline)
		#print detalle	
		#total
		factotal    = subtotal  
		totalgral	= subtotal 
		subtotal	= locale.format('%.2f',  subtotal, grouping=True)
		subtotal	= subtotal.replace(',','.')
		subtotal	= subtotal.rjust(10)
		ttcajas	= locale.format('%.0f',  ttcajas, grouping=True)
		ttcajas	= ttcajas.replace(',','.')
		ttcajas	= ttcajas.center(6)

	
	#Consulta de condiciones de pago
	#para obtener los datos del dscto aplicar.
	nb_dscto	= ''
	dscto		= 0
	vdscto		= ''
	if payment_id: 
		sql_payment = """
		SELECT t.name,t.amount
		FROM   account_payment_tax_rel	AS r
		INNER JOIN account_tax		AS t ON r.tax_id=t.id
		WHERE r.paymenterm_id=%d;"""%payment_id	
		cr.execute (sql_payment)
		reslt_payment	= cr.fetchall()
		if reslt_payment:
			nb_dscto	= reslt_payment[0][0]
			vdscto		= reslt_payment[0][1] * 100 * -1
			vdscto		= locale.format('%.0f',  vdscto, grouping=True)
			vdscto		+= ' % '
			vdscto		= vdscto.rjust(4)
	#Consulta Impuestos y/o descuentos
	tax_line	= []
	sql_i = "SELECT a.amount, a.base, a.name FROM   account_invoice_tax	AS a	WHERE a.invoice_id=%d;"%datosrefund.id 
	cr.execute (sql_i)
	reslt_invoice_tax	= cr.fetchall() 
	if reslt_invoice_tax:
		for invoice_tax in reslt_invoice_tax:
			#Se Obtiene el Grupo o tipo de Tax
			tax_id		= pooler.get_pool(cr.dbname).get('account.tax').search(cr, uid, [('name','=',invoice_tax[2]) ])
			tax_info	= pooler.get_pool(cr.dbname).get('account.tax').read(cr, uid, tax_id,['tax_group','amount'])
			if invoice_tax[2] == nb_dscto:
			    dscto	=  invoice_tax[0]
			    if dscto < 0:
			        dscto *= -1
			    totalgral	-= dscto
			if tax_info and tax_info[0]['tax_group'] == 'vat':
				tax_line.append(invoice_tax)
				totaliva  += invoice_tax[0]
				totalgral	+= invoice_tax[0]
	if dscto:	
		totaldscto	= locale.format('%.2f',  dscto, grouping=True)
		totaldscto	= totaldscto.replace(',','.')
		totaldscto	= totaldscto.rjust(10)
		factotal    -= dscto
	else:
	    vdscto		= ''	
	factotal	= locale.format('%.2f',  factotal, grouping=True)
	factotal	= factotal.replace(',','.')
	factotal	= factotal.rjust(10)	
	totalpagar	= locale.format('%.2f',  totalgral, grouping=True)
	totalpagar	= totalpagar.replace(',','.')
	totalpagar	= totalpagar.rjust(10)			 		
	#Consulta de Notas de Atencio de la Factura
	cnt		= 0
	ntline	= notas_at 
	#Archivo ======================================================================================
	filename	= ruta+'nc'+str(datosrefund.id)+'.txt'
	output		= codecs.open(filename,"w", "cp850")
	#Datos Generales	
	output.write(" \n")
	output.write(" \n")
	#output.write(boldon)
	output.write(normal+'NOTA DE CREDITO\n'.rjust(79))
	output.write(' '.rjust(64) + nrof.center(15) + '\n')
	output.write(" \n")
	output.write(" \n")
	output.write(comprime+'NOMBRE/RAZON SOCIAL:'.ljust(60)+'CLIENTE Y DIRECCION DE ENTREGA:'.ljust(40)+' ZONA'.ljust(20)+'CODIGO CLIENTE'.ljust(30)+'MES\n')	
	output.write(rsocial+cliente+'  '+zona+codcli+mes+'\n')	
	output.write('DIRECCION FISCAL: '.ljust(60)+dir_ent1+' VENDEDOR'.ljust(40)+'CONDICIONES\n')
	output.write(dir_fis1+'  '+dir_ent2+vendedor+cpago+'\n')	
	output.write(dir_fis2+dir_ent3+'Fecha Factura:    Factura Nro.       Bs Factura:\n')
	output.write(dir_fis3+cdad_ent+fechap+nrop+monto_fact+'\n')
	output.write(loc_fis+edo_ent+'Fecha Nota:'+fechaf+' Guia Nro.:'+ nrog +'\n')
	output.write('Telefono: '+tlf_fis+'   '+tlf_ent+'\n')
	output.write('RIF: '+rifcli+'\n')
	#output.write(boldoff)
	
	#Datos del Detalle
	output.write(normal+"-------------------------------------------------------------------------------\n")	
	encab = 'CODIGO     PRODUCTO                    REF.   CAJAS    PRECIO     IMPORTE   %'
	output.write(normal+encab+'\n')  
	output.write(normal+"-------------------------------------------------------------------------------\n")
	for d in detalle:
		output.write(d)
		
	#Total Cajas
	output.write(' \n')
	output.write(normal+'             TOTAL CAJAS                     '+ ttcajas +'\n')
	#Notas de Atencion
	output.write('\n')
	output.write(ntline+"\n")	
	
	#Saltos de Linea
	cont = cdet + cnt
	for i in range(29 - cont):
		output.write('\n')
			
	#Nota pie de pagina
	output.write(normal+'El Precio Facturado Incluye Toda la Mercancia Despachada \n')
	output.write(normal+"-------------------------------------------------------------------------------\n")
	output.write(comprime+'MOTIVO DE LA DEVOLUCION \n')
	
	#Totales 	
	output.write(comprime+'1) Producto Agotado         6) Cliente Ausente                                        '  + normal + '       TOTAL N.C       Bs.'+ subtotal + '\n')
	output.write(comprime+'2) Error Facturacion        7) Direccion Insuficiente                               ' + normal + '       Menos Dcto.     '+vdscto+' '+ totaldscto+ '\n')	
	output.write(comprime+'3) Rechazado por el Cliente 8) Facturar de Nuevo                                    '+ normal + '         Subtotal       Bs.'+ factotal + '\n')
	output.write(comprime+'4) Facturado Dos Veces      9) Producto Descontinuado    \n')
	space_b ='                                                '	
	for t in tax_line:
		mnt_iva	= locale.format('%.2f',  t[0], grouping=True)
		mnt_iva	= mnt_iva.replace(',','.')
		mnt_iva	= mnt_iva.rjust(10)
		nb_iva = t[2]
		output.write(comprime+'5) Unica Forma de Pago     10) Varios                                                 '+normal+'       IVA  12%           '+mnt_iva+'\n')
	output.write(normal+'                           Recibido Conforme    '+ normal + '   Total Neto     Bs.'+ totalpagar + '\n')
	output.write(saltopag) 
	output.close()
	#get name printer
	printer_obj	=  pooler.get_pool(cr.dbname).get('ir.printers').read(cr, uid, form['printer'], ['printer'])
	
	comando		= "lpr -P " + printer_obj['printer'] + ' ' + filename 
	salida,estado	=commands.getstatusoutput(comando) 
	return {'resultado':"OK...!"}
	
class refund_prints(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : range_form, 'fields' : TheFields, 'state' : [('end', 'Cancel'),('report', 'Imprimir') ]}
		},
		'report' :  {
			'actions' : [_invoice_print],
			'result': {'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
		},		
	}

refund_prints("refund_print")
