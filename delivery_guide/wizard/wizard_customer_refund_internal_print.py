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

#Formulario del Wizard - Datos Entrada------------------------------------------------------------------------------------------------
range_form = '''<?xml version="1.0"?>
<form string="Imprimir Notas Credito Interna">
	<separator colspan="2" string="Indique los Datos"/>
	<newline/>
	<field name="printer"/>
	<field name="invoice"/>
</form>'''

TheFields = {
	'printer': {'string':'Impresora', 'type':'many2one','relation': 'ir.printers', 'required':True,  'size':90 },
	'invoice': {'string':'Nota Credito Nro.', 'type':'many2one','relation': 'account.invoice', 'required':True,  'size':90,  'domain':[('type','=','out_refund'),('internal','=',1)] },
}


#Formulario del Wizard - Datos Salida-------------------------------------------------------------------------------------------------
_result_form = '''<?xml version="1.0"?>
<form string="Informacion">
	<field name="resultado"/>
</form>''' 

_result_fields = {
	'resultado': {'string': 'Resultado','type': 'char','readonly': True, 'size':200},
} 


#Funcion para el formato de Cadenas de Caracteres ------------------------------------------------------------------------------------
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


def _refund_print_internal(self, cr, uid, data, context):
	#####Variables ---------------------------------------------------------------------------------------------------------------
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
	codcli	= ''.center(30)
	mes		= ''
	rsocial	= ''.ljust(60)
	dir_ent2	= ''.ljust(40)
	dir_fis1	= ''.ljust(58)
	dir_ent3	= ''.ljust(40)
	vendedor	= ''.ljust(40)	
	cpago	= ''.center(20)
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
	totaldscto	= ''.rjust(12)
	#
	#
	#####--------------------------------------------------------------------------------------------------------------------
	if not data:
		return {'resultado':"No hay datos...!"}	
	#####Consulta de datos generales de la Factura------------------------------------------------------------------------------------------------------
	#
	#
	form = data['form']
	sql = """
	SELECT f.id,f.parent_id,f.partner_id,payment_term,f.name,f.reference,f.date_invoice,p.ref,p.vat,p.name,z.name,
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
		idfact		= datosg[0]                                         #ID. Nota Credito
		idfa		= datosg[1]	                                        #ID. Guia
		nrof		= _set_format_string(datosg[4],15,'center')			#Nro. Nota Credido
		mes			= _set_format_string('',6,'center')					#Mes  
		nrop		= _set_format_string(datosg[5],20,'ljust')			#Nro. Factura Afectada
		f		    = datosg[6].split('-')
		fechaf		= f[2] +'-' + f[1] +'-' + f[0]
		fechaf		= _set_format_string(fechaf,20,'ljust')			#Fecha Nota Cred
		ffa		    = _set_format_string('',20,'ljust')					#Fecha Factura
		codcli		= _set_format_string(datosg[7],30,'center')			#Codigo del Cliente
		cliente		= _set_format_string(datosg[9],40,'ljust')			#Nombre del Cliente o Negocio
		rifcli		= _set_format_string(datosg[8],60,'ljust')			#Rif Cliente
		zona		= _set_format_string(datosg[10],18,'ljust')			#Zona del Cliente
		rsocial		= _set_format_string(datosg[11],60,'ljust')			#Razon Social del Cliente
		tlf_fis		= _set_format_string(datosg[12],60,'ljust')			#Telefono		
		dir_fis1	= _set_format_string(datosg[13],58,'ljust')			#Direccion Fiscal
		dir_fis3	= _set_format_string(datosg[14],60,'ljust')			#
		cpago		= _set_format_string(datosg[17],20,'center')		#Condiciones de Pago
		notas_at	= datosg[18]										#Notas Atencion Manual
		payment_id	= datosg[19]										#ID Condiciones de Pago
		totalpagar	= ''.rjust(11)										#Total Pagar Factura

		##Validaciones tamaño del String--------------------------------------------------------------		
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

        #Periodo Facturacion----------------------------------------------------------------------------------------
		pgp_obj = pooler.get_pool(cr.dbname).get('period.generalperiod')
		pgp_ids = pgp_obj.find(cr, uid,datosg[6], tp='sale')
		if pgp_ids:
		    pg = pgp_obj.browse(cr, uid, pgp_ids)[0]
		    mes = _set_format_string(pg.code,6,'center')

		#Vendedor -----------------------------------------------------------------------------------
		vendedor_id		= pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',datosg[10]),('salesman', '=', 1) ])
		if vendedor_id:
			nomb	= pooler.get_pool(cr.dbname).get('res.partner').read(cr, uid, vendedor_id,['name'])[0]['name']
			vendedor = _set_format_string(nomb,40,'ljust')

		##Se obtiene la Fecha Factura Afectada----------------------------------------------------------------------
		if idfa:  		
		    fa_dat		= pooler.get_pool(cr.dbname).get('account.invoice').read(cr, uid, [idfa],['date_invoice'])
		    if fa_dat and fa_dat[0]:
		        ffa     = fa_dat[0]['date_invoice']
		        fechafa = ffa.split('-')
		        ffa		= fechafa[2] +'-' + fechafa[1] +'-' + fechafa[0]
		        ffa  = ffa.ljust(20)
					
		##Datos de Direccion de Entrga----------------------------------------------------------------------
		##Consulta de datos entrega
		sqle = """
		SELECT d.street,d.street2,d.phone,s.name,c.name    
		FROM res_partner_address 	AS d
		LEFT JOIN res_country_state	AS s ON d.state_id=s.id 
		LEFT JOIN res_state_city		AS c ON d.city_id=c.id 
		WHERE partner_id=%d AND d.type='delivery';"""%datosg[2]
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
	#
	#####--------------------------------------------------------------------------------------------------------------

	#####Consulta de datos Detalle de la Factura---------------------------------------------------------------------------------------------------------------------------
	#
	#
	sqlp = """
	SELECT id,name,quantity,price_unit   
	FROM account_invoice_line 
	WHERE invoice_id=%d;"""%datosg[0]
	cr.execute (sqlp)
	result_d	= cr.fetchall()
	detalle	= []
	cdet	= 0
	if result_d:
		for inf in result_d:
			total	= 0
			iva		= 0		
			if (inf[2] > 0) and (inf[3] > 0):
				total 	= inf[2]*inf[3]
				subtotal	+= total 
				importe	= locale.format('%.2f',  total, grouping=True)
				importe	= importe.replace(',','.')
			descrip	= inf[1] 						
			descrip	= _set_format_string(descrip,96,'ljust')		#Referencia
			#cantidad	= locale.format('%.0f',  0, grouping=True)	#Cantidad
			#cantidad	= cantidad.replace(',','.')					#
			cantidad	= ' '.center(5)						#
			#precio	= locale.format('%.2f',  inf[3], grouping=True)	#
			#precio	= precio.replace(',','.')					#Precio Unitario
			importe 	= importe.rjust(12)							#Total 
										#Iva
			#Se consulta el valor del iva por producto----------------------------------------------
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
				iva	= iva.center(6)
				precio	= ' '.rjust(8)
			else:
			    iva		= '0'.center(6)
			    precio	= ' (E)'.rjust(8)
			#-----------------------------------------------------------------------------------------
			detline	= comprime+ descrip+normal+cantidad+precio+importe+iva+'\t\n'
			cdet		+= 1
			detalle.append(detline)
		#print detalle	
		#total
		factotal    = subtotal  
		totalgral	= subtotal 
		subtotal	= locale.format('%.2f',  subtotal, grouping=True)
		subtotal	= subtotal.replace(',','.')
		subtotal	= subtotal.rjust(12)
	
	nb_dscto	= ''
	dscto		= 0
	vdscto		= ''
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
			if tax_info[0]['tax_group'] != 'vat':
			    dscto	=  invoice_tax[0]
			    vdscto		= tax_info[0]['amount'] * 100 * -1
			    vdscto		= locale.format('%.0f',  vdscto, grouping=True)
			    vdscto		+= ' % ' 
			    vdscto		= vdscto.rjust(4)
			    if dscto < 0:
			        dscto *= -1
			    totalgral	-= dscto
			if tax_info[0]['tax_group'] == 'vat':
				tax_line.append(invoice_tax)
				totaliva  += invoice_tax[0]
				totalgral	+= invoice_tax[0]
	if dscto:	
		totaldscto	= locale.format('%.2f',  dscto, grouping=True)
		totaldscto	= totaldscto.replace(',','.')
		totaldscto	= totaldscto.rjust(12)
		factotal    -= dscto

	factotal	= locale.format('%.2f',  factotal, grouping=True)
	factotal	= factotal.replace(',','.')
	factotal	= factotal.rjust(12)	
	totalpagar	= locale.format('%.2f',  totalgral, grouping=True)
	totalpagar	= totalpagar.replace(',','.')
	totalpagar	= totalpagar.rjust(12)			 		
	#--------------------------------------------------------------------------------------------------------------------
	
	#####Consulta de Notas de Atencio de la Factura---------------------------------------------------------------------------------------------------------------------------
	#
	#
	detnota 	= []
	cnt		= 0
	ntline	= ''.rjust(5) 
	if notas_at:
		ntline += notas_at
	#------------------------------------------------------------------------------------------------------------------	
	
	
	#Archivo ================================================================================================================
	filename	= ruta+'inc'+datosg[4]+'.txt'
	output		= codecs.open(filename,"w", "utf-8")
	#	
	#Datos Generales--------------------------------------------------------------------------------------------------------------------------------------------------	
	output.write(" \t\n")
	output.write(" \t\n")
	#output.write(boldon)
	output.write(normal+'NOTA CREDITO\t\n'.rjust(84))
	output.write(' '.rjust(69) + nrof.center(15) + '\t\n')
	output.write(" \t\n")
	output.write(" \t\n")
	output.write(comprime+'NOMBRE/RAZON SOCIAL:'.ljust(60)+'DIRECCION ENTREGA:'.ljust(40)+' ZONA'.ljust(20)+'CODIGO CLIENTE'.ljust(30)+'MES\t\n')	
	output.write(rsocial+cliente+'  '+zona+codcli+mes+' \t\n')	
	output.write('DIRECCION FISCAL: '.ljust(60)+dir_ent1+' VENDEDOR'.ljust(40)+'CONDICIONES\t\n')
	output.write(dir_fis1+'  '+dir_ent2+vendedor+cpago+' \t\n')	
	output.write(dir_fis2+dir_ent3+'Fecha Fact.:     Factura:          Fecha N/C:    \t\n')
	output.write(dir_fis3+cdad_ent+ffa+nrop+fechaf+'\t\n')
	output.write(loc_fis+edo_ent+' \t\n')
	output.write('Telefono: '+tlf_fis+'   '+tlf_ent+' \t\n') 
	output.write('RIF: '+rifcli+' \t\n')
	#output.write(boldoff)
	
	#Datos del Detalle--------------------------------------------------------------------------------------------------------------------------------------------------
	output.write("----------------------------------------------------------------------------------------------------------------------------------------------------------------\t\n")	
	encab = 'DESCRIPCION                                                       IMPORTE     %'
	output.write(normal+encab+' \t\n')  
	output.write(comprime+"----------------------------------------------------------------------------------------------------------------------------------------------------------------\t\n")
	for d in detalle:
		output.write(d)
	
	#Total Cajas
	output.write(' \t\n')	
	#Notas de Atencion-------------------------------------------------------------------------------------------------------------------------------------------------
	output.write(' \t\n')
	output.write(ntline+" \t\n")	
	
	#Saltos de Linea-----------------------------------------------------------------------------------------------------------
	cont = cdet + cnt
	for i in range(29 - cont):
		output.write(' \t\n')
			
	#Nota pie de pagina ----------------------------------------------------------------------------------------------------------------------------------------------------------------
	output.write(comprime+"----------------------------------------------------------------------------------------------------------------------------------------------------------------\t\n")
	output.write(comprime+'FORMA DE PAGO: CHEQUE \t\n')
	#Totales ----------------------------------------------------------------------------------------------------------------------------------------------------------------	
	output.write(comprime+'                                                                                      '  + normal + '     SUB-TOTAL         Bs.'+ subtotal + '\t\n')
	output.write(comprime+'                                                                                    ' + normal + '      Menos Dcto.      '+vdscto+' '+ totaldscto+ '\t\n')
	output.write(comprime+'                                                                                    '+ normal + '      Total Nota Cred.  Bs.'+ factotal + '\t\n')
	output.write(comprime+' \t\n') 
	space_b ='                                                '	
	for t in tax_line:
		mnt_iva	= locale.format('%.2f',  t[0], grouping=True)
		mnt_iva	= mnt_iva.replace(',','.')
		mnt_iva	= mnt_iva.rjust(12)
		nb_iva = t[2].rstrip()
		output.write(comprime+'                                                                                      '+normal+'     I.V.A  12%           '+mnt_iva+'\t\n')
	output.write(normal+'                           Recibido Conforme    '+ normal + 'Total Neto      Bs.  '+ totalpagar + '\t\n')
	output.write(saltopag) 
	output.close()
	#==========================================================================================================================
	#
	#Imprimiendo Factura------------------------------------------------------------------------------------------------
	#get name printer
	printer_obj	=  pooler.get_pool(cr.dbname).get('ir.printers').read(cr, uid, form['printer'], ['printer'])
	
	comando		= "lpr -P " + printer_obj['printer'] + ' ' + filename  
	vals = {'printed':True}
	pooler.get_pool(cr.dbname).get('account.invoice').write(cr, uid, [idfact], vals)
	salida,estado	=commands.getstatusoutput(comando)   
	return {'resultado':"OK...!"}
	
class internal_refund_prints(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : range_form, 'fields' : TheFields, 'state' : [('end', 'Cancel'),('report', 'Imprimir') ]}
		},
		'report' :  {
			'actions' : [_refund_print_internal],
			'result': {'type':'form', 'arch':_result_form, 'fields':_result_fields, 'state':[('end','OK')]}
		},		
	}

internal_refund_prints("internal_invoice_refund_print")
