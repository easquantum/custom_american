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
<form string="Imprimir Factura Especiales">
	<separator colspan="2" string="Indique los Datos"/>
	<newline/>
	<field name="printer"/>
	<field name="invoice"/>
</form>'''

TheFields = {
	'printer': {'string':'Impresora', 'type':'many2one','relation': 'ir.printers', 'required':True,  'size':90 },
	'invoice': {'string':'Factura', 'type':'many2one','relation': 'account.invoice', 'required':True,  'size':90,  'domain':[('type','=','out_invoice'),('printed','=',0)] },
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


def _invoice_print_esp(self, cr, uid, data, context):
	#####Variables
	#
	#	
	boldon	= chr(27)+chr(69)
	boldoff	= chr(27)+chr(70)	
	comprime	= chr(15)+chr(27)+'M'
	normal	= chr(18)+chr(27)+'P'
	saltopag	= chr(12)
	ruta	= "/home/public/" # Ruta Desarrollo
	ruta	= "/opt/openerp/reportes/ventas/" # Ruta Server Produccion
	spacios_bnc = ''
	guia_nro = ''
	nrof	= ''.center(15)
	cliente	= ''.ljust(40)
	dir_ent1	= ''.ljust(40)
	zona		= ''.ljust(20)
	codcli	= ''.center(27)
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
	payment_id= 0
	totaldscto	= ''.rjust(10)
	if not data:
		return {'resultado':"No hay datos...!"}	
	#Consulta de datos generales de la Factura
	form = data['form']
	sql = """
	SELECT f.id,f.guide_id,f.partner_id,payment_term,f.name,f.reference,f.date_invoice,p.ref,p.vat,p.name,z.name,
	       d.name,d.phone,d.street,d.street2,s.name,c.name,t.name,f.nota_atencion,t.id    
	FROM account_invoice			AS f
	INNER JOIN res_partner			AS p ON f.partner_id=p.id
	INNER JOIN res_partner_address	AS d ON p.id=d.partner_id
	LEFT JOIN res_partner_zone		AS z ON p.code_zone_id=z.id
	LEFT JOIN res_country_state		AS s ON d.state_id=s.id
	LEFT JOIN res_state_city		AS c ON d.city_id=c.id
	LEFT JOIN account_payment_term	AS t ON f.payment_term=t.id
	WHERE f.id=%d AND d.type='default';"""%form['invoice']
	#print sql
	cr.execute (sql)
	result = cr.fetchall()
	datosg = result[0] 
	#print datosg
	if datosg:
		idfact		= datosg[0]                                         #ID. Factura
		nrof		= datosg[4]                                         #Nro. Factura
		mes			= _set_format_string('',3,'center')					#Mes Factura 
		#nrop		= _set_format_string(datosg[5],20,'ljust')			#Nro. Pedido
		f		    = datosg[6].split('-')
		fechaf		= f[2] +'-' + f[1] +'-' + f[0]                      #Fecha Factura			
		#fechap		= _set_format_string('',20,'ljust')					#Fecha Pedido
		codcli		= _set_format_string(datosg[7],30,'center')			#Codigo del Cliente
		cliente		= _set_format_string(datosg[9],40,'ljust')			#Nombre del Cliente o Negocio
		rifcli		= _set_format_string(datosg[8],60,'ljust')			#Rif Cliente
		zona		= _set_format_string(datosg[10],18,'ljust')			#Zona del Cliente
		rsocial		= _set_format_string(datosg[11],60,'ljust')			#Razon Social del Cliente
		tlf_fis		= _set_format_string(datosg[12],60,'ljust')			#Telefono		
		dir_fis1	= _set_format_string(datosg[13],58,'ljust')			#Direccion Fiscal
		dir_fis3	= _set_format_string(datosg[14],60,'ljust')			#
		cpago		= _set_format_string(datosg[17],15,'center')		#Condiciones de Pago
		notas_at	= datosg[18]										#Notas Atencion Manual
		payment_id	= datosg[19]										#ID Condiciones de Pago
		totalpagar	= ''.rjust(11)										#Total Pagar Factura

		##Validaciones tamaño del String 		
		if len(datosg[13]) > 58:
			dir_fis2	= datosg[13][58:120]
			dir_fis2	= dir_fis2.ljust(60)
		if datosg[15]:
			loc_fis	= datosg[15]                #Estado 
		if datosg[16]:
			loc_fis	+= ' '+datosg[16]           #Ciudad 
		
		if loc_fis:
		    loc_fis = _set_format_string(loc_fis,60,'ljust')
		else:
		    loc_fis = '  '.ljust(60)
					
		##Datos de Direccion de Entrga----------------------------------
		#datos_e	= reslt[0] 		
		#dir_ent1	= _set_format_string(datos_e[0],40,'ljust')
		#dir_ent3	= _set_format_string(datos_e[1],40,'ljust')
		#tlf_ent		= _set_format_string(datos_e[2],40,'ljust')
		#edo_ent		= _set_format_string(datos_e[3],40,'ljust')
		#cdad_ent	= _set_format_string(datos_e[4],40,'ljust')
		#dir_ent2	= _set_format_string(datos_e[0][41:81],40,'ljust')
	#Consulta de datos Detalle de la Factura
	sqlp = """
	SELECT id,name,quantity,price_unit   
	FROM account_invoice_line 
	WHERE invoice_id=%d;"""%datosg[0]
	cr.execute (sqlp)
	result_d	= cr.fetchall()
	detalle	= []
	cdet	= 0
	ttcajas = 0
	if result_d:
		for inf in result_d:
			total	= 0
			iva	= 0		
			if (inf[2] > 0) and (inf[3] > 0):
				total 	= inf[2]*inf[3]
				subtotal	+= total 
				importe	= locale.format('%.2f',  total, grouping=True)
				importe	= importe.replace(',','.')
			descrip	= inf[1] 						
			descrip	= _set_format_string(descrip,96,'ljust')								#Referencia
			cantidad	= locale.format('%.0f',  inf[2], grouping=True)	#Cantidad
			cantidad	= cantidad.replace(',','.')					#
			cantidad	= cantidad.center(4)						#
			precio	= locale.format('%.2f',  inf[3], grouping=True)	#
			precio	= precio.replace(',','.')					#Precio Unitario
			importe 	= importe.rjust(12)							#Total 
			ttcajas += inf[2]
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
			if not iva:
			    iva = '0'.center(4)
			    precio	+= ' (E)'
			    precio	= precio.rjust(14)
			    importe 	= importe.rjust(8)
			detline	= comprime+ descrip+normal+cantidad+precio+importe+iva+'\n'
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
			vdscto		= vdscto.rjust(3)
	#Consulta Impuestos y/o descuentos
	tax_line	= []
	sql_i = "SELECT a.amount, a.base, a.name FROM   account_invoice_tax	AS a	WHERE a.invoice_id=%d;"%datosg[0] 
	cr.execute (sql_i)
	reslt_invoice_tax	= cr.fetchall() 
	if reslt_invoice_tax:
		for invoice_tax in reslt_invoice_tax:
			#Se Obtiene el Grupo o tipo de Tax
			tax_id		= pooler.get_pool(cr.dbname).get('account.tax').search(cr, uid, [('name','=',invoice_tax[2]) ])
			tax_info	= pooler.get_pool(cr.dbname).get('account.tax').read(cr, uid, tax_id,['tax_group','amount'])
			if tax_info[0]['tax_group'] == 'vat':
				tax_line.append(invoice_tax)
				totaliva  += invoice_tax[0]
				totalgral	+= invoice_tax[0]
	
	factotal	= locale.format('%.2f',  factotal, grouping=True)
	factotal	= factotal.replace(',','.')
	factotal	= factotal.rjust(10)	
	totalpagar	= locale.format('%.2f',  totalgral, grouping=True)
	totalpagar	= totalpagar.replace(',','.')
	totalpagar	= totalpagar.rjust(10)
	#Consulta de Notas de Atencio de la Factura
	detnota 	= []
	cnt		= 0
	ntline	= ''.rjust(5) 
	if notas_at:
		ntline += notas_at 	
	sqln = """
	SELECT n.code,n.name    
	FROM account_nota_atencion_rel	AS r
	INNER JOIN nota_atencion			AS n ON r.nota_atencion_id=n.id
	WHERE r.invoice_id=%d;"""%datosg[0]
	cr.execute (sqln)
	result_n 	= cr.fetchall()
	if result_n:
		cnt		+= 1
		for nt in result_n:
			ntline	+= '  N-A='+nt[0]
	#Archivo ======================================================================================
	filename	= ruta+'f'+datosg[4]+'.txt'
	output		= codecs.open(filename,"w", "cp850")
	#Datos Generale	
	output.write("\n")
	output.write("\n")
	output.write(boldon)
	output.write(normal+'F A C T U R A\n'.rjust(79))
	output.write(' '.rjust(64) + nrof.center(15) + '\n')
	output.write("\n")
	output.write("\n")
	output.write(comprime+'NOMBRE/RAZON SOCIAL:'.ljust(60)+'CLIENTE Y DIRECCION DE ENTREGA:'.ljust(40)+' ZONA'.ljust(20)+'CODIGO CLIENTE'.center(30)+'MES\n')	
	output.write(rsocial+cliente+'  '+zona+codcli+mes+' \n')	
	output.write('DIRECCION FISCAL: '.ljust(60)+dir_ent1+'        '.ljust(40)+'CONDICIONES\n')
	output.write(dir_fis1+'  '+dir_ent2+vendedor+cpago+'\n') 	
	output.write(dir_fis2+dir_ent3+'                                   Fecha Factura:\n')
	output.write(dir_fis3+cdad_ent+fechap+nrop+fechaf+'\n')
	output.write(loc_fis+edo_ent+'\n')
	output.write('Telefono: '+tlf_fis+'   '+tlf_ent+' \n') 
	output.write('RIF: '+rifcli+'\n')
	output.write(boldoff)
	
	#Datos del Detalle
	output.write(normal+"-------------------------------------------------------------------------------\n")	
	encab = 'DESCRIPCION                                     CAJAS     PRECIO     IMPORTE  %'
	output.write(normal+encab+'\n')  
	output.write(normal+"-------------------------------------------------------------------------------\n")
	for d in detalle:
		output.write(d)
	
	#Total Cajas
	output.write('\n')
	output.write(normal+'             TOTAL CAJAS                       '+ ttcajas +'\n') 	
	#Notas de Atencion
	output.write(' \n')
	output.write(ntline+" \n")	
	
	#Saltos de Linea
	cont = cdet + cnt
	for i in range(29 - cont):
		output.write(' \n')
			
	#Nota pie de pagina 
	output.write(normal+'El Precio Facturado Incluye Toda la Mercancia Despachada \n')
	output.write(comprime+'Emitir cheque No Endosable a nombre de: "American Distribution de Venezuela C.A."\n')
	output.write(normal+"-------------------------------------------------------------------------------\n")
	
	#Totales 	
	output.write(comprime+'IMPORTANTE: Este orifinal no es valido como cancelacion de COBRO en VENTAS A CREDITO' + normal + '      TOTAL FACTURA    Bs.'+ subtotal + '\n')
	output.write(comprime+'Al cancelar Factura a Credito favor exigir RECIBO OFICIAL unico que reconocemos como' + normal + '\n')
	output.write(comprime+'COMPROBANTE DE PAGO. Para pago al recibo de mercancia (pago contra transporte)'+ normal + '             Subtotal     Bs.'+ factotal + '\n')
	output.write(comprime+'autorizados la cancelacion de este original \n') 
	space_b ='                                                '	
	for t in tax_line:
		mnt_iva	= locale.format('%.2f',  t[0], grouping=True)
		mnt_iva	= mnt_iva.replace(',','.')
		mnt_iva	= mnt_iva.rjust(12)
		nb_iva = t[2].rstrip()
		output.write(normal+space_b+nb_iva+'            '+mnt_iva+'\n')
	output.write(comprime+'FORMA DE PAGO: CHEQUE                                    Recibido Conforme         ' + normal + '         Total Neto    Bs.'+ totalpagar + '\n')
	output.write(saltopag) 
	output.close()
	#Imprimiendo Factura
	#get name printer
	printer_obj	=  pooler.get_pool(cr.dbname).get('ir.printers').read(cr, uid, form['printer'], ['printer'])
	
	comando		= "lpr -P " + printer_obj['printer'] + ' ' + filename  
	vals = {'printed':True}
	pooler.get_pool(cr.dbname).get('account.invoice').write(cr, uid, [idfact], vals)
	salida,estado	=commands.getstatusoutput(comando)   
	return {'resultado':"OK...!"}
	
class espec_invoice_prints(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : range_form, 'fields' : TheFields, 'state' : [('end', 'Cancel'),('report', 'Imprimir') ]}
		},
		'report' :  {
			'actions' : [_invoice_print_esp],
			'result': {'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
		},		
	}

espec_invoice_prints("esp_invoice_print")
