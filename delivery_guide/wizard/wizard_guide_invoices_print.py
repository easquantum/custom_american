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

import sys
import time
import locale
import commands
import wizard
import netsvc
import pooler
import tools
from osv.orm import browse_record
import codecs

#Inicializacion de Variebles Globales
list_print_file = []

#Formulario del Wizard - Datos Entrada
datos_form = '''<?xml version="1.0"?>
<form string="Imprimir Guia">
	<separator colspan="2" string="Indique los Datos"/>
	<newline/>
	<field name="printer"/>
	<field name="guide"/>

	<separator colspan="4" string="Facturas de la Guia:"/>
	<field name="facturas"/>
</form>'''

datos_fields = {
	'printer': {'string':'Impresora', 'type':'many2one','relation': 'ir.printers', 'required':True,  'size':90 },
	'guide': {'string':'Guia Nro.', 'type':'many2one','relation': 'delivery.guide', 'required':True,  'size':90,  'domain':[('traspaso','=',0),('printed','=',0)] }, #done draft
	'facturas': {'string':"Imprimir Facturas",'type':'boolean'}
}


#Formulario del Wizard - Datos Salida
result_form = '''<?xml version="1.0"?>
<form string="Informacion">
	<field name="resultado"/>
</form>''' 

result_fields = {
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

def _invoice_print(cr,uid,invoice_id,impresora):
	if not invoice_id and impresora:
		return 	
	#####Variables---------------------------------------------------------------------------------
	#
	#	
	boldon	= chr(27)+chr(69)
	boldoff	= chr(27)+chr(70)	
	comprime	= chr(15)+chr(27)+'M'
	normal	= chr(18)+chr(27)+'P'
	saltopag	= chr(12)
	#ruta	= "/home/public/" # Ruta Desarrollo
	ruta	= "/opt/openerp/reportes/ventas/" # Ruta Server Produccion
	spacios_bnc = ''
	guia_nro = ''
	nrof	= ''.center(15)
	cliente	= ''.ljust(60)
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
	payment_id= 0
	totaldscto	= ''.rjust(10)
	#Consulta de datos generales de la Factura-------------------------------------------------
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
	WHERE f.id=%d AND d.type='default';"""%invoice_id 
	#print sql
	cr.execute (sql)
	result = cr.fetchall()
	if not result:
	    return  
	datosg = result[0] 
	if datosg:
		idfact		= datosg[0]                                         #ID. Factura
		idguia		= datosg[1]	                                        #ID. Guia
		nrof		= _set_format_string(datosg[4],15,'center')			#Nro. Factura
		mes			= _set_format_string('',3,'center')					#Mes Factura 
		nrop		= _set_format_string(datosg[5],17,'ljust')			#Nro. Pedido
		f		    = datosg[6].split('-')
		fechaf		= f[2] +'-' + f[1] +'-' + f[0]                      #Fecha Factura
		fechap		= _set_format_string('',20,'ljust')					#Fecha Pedido
		codcli		= _set_format_string(datosg[7],27,'center')			#Codigo del Cliente
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
		totalpagar	= ''.rjust(10)										#Total Pagar Factura
		guia_nro		= pooler.get_pool(cr.dbname).get('delivery.guide').read(cr, uid, [idguia],['name'])[0]['name'] 
		#Periodo Facturacion
		pgp_obj = pooler.get_pool(cr.dbname).get('period.generalperiod')
		pgp_ids = pooler.get_pool(cr.dbname).get('period.generalperiod').search(cr, uid, [('date_start','<=',datosg[6]),('date_stop', '>=', datosg[6]) ])
		if pgp_ids:
		    pg = pgp_obj.browse(cr, uid, pgp_ids)[0]
		    mes = _set_format_string(pg.code,6,'center')
		#Vendedor
		vendedor_id		= pooler.get_pool(cr.dbname).get('res.partner').search(cr, uid, [('code_zone_id','=',datosg[10]),('salesman', '=', 1) ])
		if vendedor_id:
			nomb	= pooler.get_pool(cr.dbname).get('res.partner').read(cr, uid, vendedor_id,['name'])[0]['name']
			vendedor = _set_format_string(nomb,40,'ljust') 
		##Obtener Fecha pedido-----------------------------------------------------------------------
		sqlp = """
		SELECT date_order   
		FROM sale_order_invoice_rel AS r
		INNER JOIN sale_order AS s ON r.order_id=s.id 
		WHERE r.invoice_id=%d;"""%datosg[0]
		cr.execute (sqlp)
		result_p = cr.fetchall()
		if result_p:
			f = result_p[0][0]
			f = f.split('-')
			fp = f[2] +'-' + f[1] +'-' + f[0]
			fechap  = fp.ljust(20)
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
				dir_ent2	= _set_format_string(datos_e[0][41:79],40,'ljust')
	#Consulta de datos Detalle de la Factura
	sqlp = """
	SELECT d.id,p.default_code,s.product_code,t.name,p.variants,d.quantity,d.price_unit   
	FROM account_invoice_line		AS d
	INNER JOIN product_product		AS p ON d.product_id=p.id
	INNER JOIN product_template		AS t ON p.product_tmpl_id=t.id 
	LEFT JOIN  product_supplierinfo	AS s ON t.id=s.product_id
	WHERE d.invoice_id=%d
	ORDER BY p.default_code;"""%datosg[0]
	cr.execute (sqlp)
	result_d	= cr.fetchall()
	detalle	= []
	cdet	= 0
	ttcajas = 0
	if result_d:
		for inf in result_d:
			total	= 0
			iva	= 0		
			if (inf[5] > 0) and (inf[6] > 0):
				total 	= inf[5]*inf[6]
				subtotal	+= total 
				importe	= locale.format('%.2f',  total, grouping=True)
				importe	= importe.replace(',','.')
			codigo	= inf[1].ljust(8)							#Codigo del Producto
			descrip	= ''
			if inf[2]:											#Codigo Proveedor y Nombre del Producto
				descrip	= inf[2]
			if inf[3]:
				descrip	+= ' '+inf[3]							
			descrip	= _set_format_string(descrip,56,'ljust')							
			ref		= inf[4].center(10)							        #Referencia
			cantidad	= locale.format('%.0f',  inf[5], grouping=True)	#Cantidad
			cantidad	= cantidad.replace(',','.')					
			cantidad	= cantidad.center(4)						
			precio	= locale.format('%.2f',  inf[6], grouping=True)	
			precio	= precio.replace(',','.')					         #Precio Unitario
			importe 	= importe.rjust(12)							     #Total 
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
				iva	= iva.center(5)
				precio	= precio.rjust(11)
			if not iva:
				iva	= '0'.center(4)
				precio	+= ' (E)'
				precio	= precio.rjust(14)
				importe.rjust(8)
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
			if invoice_tax[2] == nb_dscto:
				dscto	=  invoice_tax[0]
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
		totaldscto	= totaldscto.rjust(10)
		factotal    -= dscto
	
	factotal	= locale.format('%.2f',  factotal, grouping=True)
	factotal	= factotal.replace(',','.')
	factotal	= factotal.rjust(10)	
	totalpagar	= locale.format('%.2f',  totalgral, grouping=True)
	totalpagar	= totalpagar.replace(',','.')
	totalpagar	= totalpagar.rjust(10)			 		
	
	#####Consulta de Notas de Atencio de la Factura
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
	#Datos Generales	
	output.write("\n")
	output.write("\n")
	#output.write(boldon)
	output.write(normal+'F A C T U R A\n'.rjust(79))
	output.write(' '.rjust(64) + nrof.center(15) + '\n')
	output.write("\n")
	output.write("\n")
	output.write(comprime+'NOMBRE/RAZON SOCIAL:'.ljust(60)+'CLIENTE Y DIRECCION ENTREGA:'.ljust(40)+' ZONA'.ljust(20)+'CODIGO CLIENTE'.ljust(30)+'MES\n')	
	output.write(rsocial+cliente+'  '+zona+codcli+mes+'\n')	
	output.write('DIRECCION FISCAL: '.ljust(60)+dir_ent1+' VENDEDOR'.ljust(40)+'CONDICIONES\n')
	output.write(dir_fis1+'  '+dir_ent2+vendedor+cpago+'\n')	 
	output.write(dir_fis2+dir_ent3+'Fecha Pedido:    Pedido Nro.       Fecha Factura:\n')
	output.write(dir_fis3+cdad_ent+fechap+nrop+fechaf+'\n')
	output.write(loc_fis+edo_ent+' Guia Nro.:'+guia_nro+'\n')
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
	output.write('\n')
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
	output.write(comprime+'Emitir cheque No Endosable a nombre de: "American Distribution de Venezuela C.A."\n')
	output.write(normal+"-------------------------------------------------------------------------------\n")
	
	#Totales	
	output.write(comprime+'IMPORTANTE: Este orifinal no es valido como cancelacion de COBRO en VENTAS A CREDITO' + normal + '      TOTAL FACTURA    Bs.'+ subtotal + '\n')
	output.write(comprime+'Al cancelar Factura a Credito favor exigir RECIBO OFICIAL unico que reconocemos como' + normal + '      Menos Dcto.    '+vdscto+'% '+ totaldscto+ '\n')
	output.write(comprime+'COMPROBANTE DE PAGO. Para pago al recibo de mercancia (pago contra transporte)'+ normal + '              Subtotal    Bs.'+ factotal + '\n')
	output.write(comprime+'autorizados la cancelacion de este original \n') 
	space_b ='                                                     '	
	for t in tax_line:
		mnt_iva	= locale.format('%.2f',  t[0], grouping=True)
		mnt_iva	= mnt_iva.replace(',','.')
		mnt_iva	= mnt_iva.rjust(10)
		nb_iva = t[2].rstrip()
		output.write(normal+space_b+nb_iva+' %      '+mnt_iva+'\n')
	output.write(comprime+'FORMA DE PAGO: CHEQUE                                    Recibido Conforme         ' + normal + '         Total Neto    Bs.'+ totalpagar + '\n')
	output.write(saltopag) 
	output.close()
	#==============================================================================================
	#
	vals = {'printed':True}
	pooler.get_pool(cr.dbname).get('account.invoice').write(cr, uid, [idfact], vals)
	comando		= "lpr -P " + impresora + ' ' + filename  
	salida,estado	=commands.getstatusoutput(comando) 
	return

#Obtener total Cajas por Factura ---------------------------------------------------------------------------------------------------------
def _get_cajas(cr, invoice_id):
        cajas = '0'
        sql = "SELECT SUM(quantity) as cajas FROM  account_invoice_line WHERE invoice_id=%d;"%invoice_id
        cr.execute (sql)
        resultSQL = cr.fetchall()
        if resultSQL and resultSQL[0]:
            cajas = resultSQL[0][0]
        return cajas
		    

#Imprimir Guia de Despacho ---------------------------------------------------------------------------------------------------------
def _guide_print(self, cr, uid, guide_id,impresora):
	#Inicializacion de Veariables Locales----------------------------------
	boldon	= chr(27)+chr(69)
	boldoff	= chr(27)+chr(70)
	comprime	= chr(15)+chr(27)+'M'
	normal	= chr(18)+chr(27)+'P'
	saltopag	= chr(12) 
	dir	= "/home/public/"                  # Ruta local
	dir	= "/opt/openerp/reportes/ventas/"  # Ruta Server 
	spacios_bnc = ''
	placa		= ''

	
	obj_guide = pooler.get_pool(cr.dbname).get('delivery.guide')	
	#Consulta Guia---------------------------------------------------------
	datosguia = obj_guide.browse(cr, uid, guide_id)
	nroguia 	= datosguia.name
	f           = datosguia.date_guide.split('-')
	fguia		= f[2] +'-' + f[1] +'-' + f[0]
	transpor	= datosguia.carrier_company_id.name
	chofer		= datosguia.driver_id.name
	ruta		= datosguia.ruta_id.name
	almacen		= datosguia.warehouse_id.name
	#Validaciones Datos
	if datosguia.vehiculo_id.placa:
	    placa	= datosguia.vehiculo_id.placa

	#CREANDO ARCHIVO GUIA===========================================================================================================
	fileguia	= dir+'g'+nroguia+'.txt'
	output 	= codecs.open(fileguia,"w", "cp850")
	#Datos Generales	
	output.write(" \n")
	output.write(" \n")
	output.write(" \n")
	output.write(boldon + normal + 'GUIA DE DESPACHO  \n'.rjust(79))
	output.write(' '.rjust(64) + nroguia.center(15) + boldoff +'\n')
	output.write(" \n")
	output.write(" \n")
	output.write('TRANSPORTE: ' + transpor.ljust(45) + 'FECHA GUIA : ' + fguia +'\n')	
	output.write('CHOFER    : ' + chofer.ljust(45) + 'FECHA CARGA: _________\n')
	output.write('PLACA NRO.: ' + placa.ljust(45) + 'RUTA: ' + ruta +'\n')	
	output.write('ALMACEN   : ' + almacen.ljust(45) + 'DESTINO: ___________\n')
	output.write(" \n")
	output.write(normal+"-------------------------------------------------------------------------------\n")	
	output.write(normal+'FACTURA      CLIENTE                    ZONA     CONTADO     CREDITO    CAJAS\n')
	output.write(normal+"-------------------------------------------------------------------------------\n")
	
	#Facturas de la Guia
	contf = 0
	totalcontado = 0
	totalcredito = 0
	totalcajas = 0	
	for invoices in datosguia.guide_line:
		nrof		= invoices.invoice_id.name
		zona		= invoices.invoice_id.partner_id.code_zone_id.code_zone
		contado		= '0,00'
		credito		= '0,00'
		client		= invoices.invoice_id.partner_id.ref
		client		+= ' ' + invoices.invoice_id.partner_id.name
		contf 		+= 1
		cajas        = _get_cajas(cr,invoices.invoice_id.id)
		if cajas:
		    totalcajas += cajas
		monto        = invoices.invoice_id.amount_total
		cajas = locale.format('%.0f',  cajas, grouping=True)
		if invoices.invoice_id.payment_term.contado:
        		contado = locale.format('%.2f',  monto, grouping=True, monetary=True)
        		totalcontado += monto
		else:
        		credito = locale.format('%.2f',  monto, grouping=True, monetary=True)
        		totalcredito += monto
		output.write(normal + nrof.ljust(8) + comprime + client.ljust(60) + normal +  zona.center(9) + contado.rjust(11) + credito.rjust(12) + cajas.rjust(8) + '\n')

	#Productos de las Facturas de la Guia	
	output.write(" \n")
	#Total Faturas
	totalcontado = locale.format('%.2f',  totalcontado, grouping=True, monetary=True)
	totalcredito = locale.format('%.2f',  totalcredito, grouping=True, monetary=True)
	totalcajas = locale.format('%.0f',  totalcajas, grouping=True)
	output.write(comprime + ' '.ljust(60) + normal +  'TOTALES=====>'.center(19) + totalcontado.rjust(9) + totalcredito.rjust(12) + totalcajas.rjust(8) + '\n')
	output.write(" \n")	
	output.write(normal+"-------------------------------------------------------------------------------\n")	
	output.write(normal+'CODIGO   DESCRIPCION  PRODUCTO                           REFERENCIA     CAJAS\n')
	output.write(normal+"-------------------------------------------------------------------------------\n")

	totalcajas	= 0
	totalpeso	= 0
	contp		= 0
	pag         = 1
	sqlp = """
	SELECT  p.default_code,s.product_code,t.name,p.variants,SUM(r.quantity) AS cantidad,t.weight_net  
	FROM	delivery_guide_line    	 AS d
	INNER  JOIN account_invoice_line AS r	 ON d.invoice_id=r.invoice_id
	INNER  JOIN product_product 	 AS p	 ON r.product_id=p.id
	INNER  JOIN product_template 	 AS t	 ON p.product_tmpl_id=t.id
	LEFT  JOIN  product_supplierinfo AS s ON t.id=s.product_id
	WHERE d.guide_id=%d
	GROUP BY p.default_code,s.product_code,t.name,p.variants,t.weight_net 
	ORDER BY p.default_code;"""%guide_id
	cr.execute (sqlp)
	resultSQL = cr.fetchall()
	for product in resultSQL:
		peso		= 0
		codigo		= ''.ljust(8)  #self._set_format_string('',10,'ljust')
		producto	= ''
		ref			= ''.center(8)
		cajas		= '0'.rjust(8)
		if product[0]:
			codigo = product[0].ljust(8)
		if product[1]:
			producto = product[1]
		if product[2]:
			producto += unicode(product[2])
		if product[3]:
			ref = product[3].center(10)
		if product[4]:
			cajas = locale.format('%.0f',  product[4], grouping=True)
			cajas = cajas.rjust(8)
			totalcajas += product[4]		
		if product[5]: 
			peso = product[5] * product[4]
			totalpeso += peso
		producto	= producto.ljust(102)
		#print "LINE",codigo+producto+ref+cajas
		output.write(normal+codigo+comprime+producto+normal+ref+cajas +'\n') 
		contp += 1
		tlineas = 36
		if pag == 1:
		    tlineas = 36 - contf  
		if contp >= tlineas:
		    pag += 1 
		    #SALTO DE PAGINA:Se Imprime el Encabezado Nuevament
		    saltosln = 0
		    limt = 8
		    if pag > 2:
		        limt += 7
		    while saltosln < limt:
		        saltosln    += 1
		        output.write("\n")
		    #Datos Generales
		    output.write(" \n")
		    output.write(" \n")
		    output.write(" \n")
		    output.write(" \n")
		    output.write(boldon + normal + 'GUIA DE DESPACHO\n'.rjust(79))
		    output.write(' '.rjust(64) + nroguia.center(15) + boldoff +'\n')
		    output.write(" \n")
		    output.write(" \n")
		    output.write('TRANSPORTE: ' + transpor.ljust(45) + 'FECHA GUIA : ' + fguia +'\n')
		    output.write('ALMACEN   : ' + almacen.ljust(50) + '\n')
		    output.write("Pag.  ".rjust(50) + str(pag)+ "\n")
		    output.write(" \n")
		    output.write(" \n")
		    output.write(normal+"-------------------------------------------------------------------------------\n")
		    output.write(normal+'CODIGO   DESCRIPCION  PRODUCTO                           REFERENCIA     CAJAS\n')
		    output.write(normal+"-------------------------------------------------------------------------------\n")
		    contp = 1

	
	#Totales
	totalcajas = locale.format('%.0f',  totalcajas, grouping=True)
	totalpeso = locale.format('%.2f',  totalpeso, grouping=True, monetary=True)
	output.write(" \n")
	output.write(" \n")
	output.write('Total Cajas  ==================>> '.ljust(65) + 	totalcajas.rjust(11) +'\n')
	output.write('Total Peso   ==================>> '.ljust(65) + 	totalpeso.rjust(11) +'\n')		
	
	#Saltos de Linea
	cnt = contp + contf
	#print 'GD CONtF',cnt,contp,contf
	if pag > 1:
	    cnt = contp
	    #print 'GD:Pasa',pag,cnt 
	for i in range(32 - cnt):
		output.write(' \n')
		
	#Pie de Pahina
	output.write(comprime+'NOTA: El transporte es responsable de la mercancia y las facturas relacionadas en la presente Guia,                 DESPACHADO POR: __________________\n')
	output.write(comprime+'hasta su total liquidacion o reclamacion por parte de los clientes o de American Distribution de Venezuela C.A.     RECIBIDO   POR: __________________\n')
	output.write(comprime+'SIN DERECHO A CREDITO FISCAL                                                                                        AUTORIZADO POR: __________________\n')
	output.close()
	imprimir		= "lpr -P " + impresora + ' ' + fileguia  
	salida,estado	= commands.getstatusoutput(imprimir) 
	wf_service = netsvc.LocalService("workflow") 
	wf_service.trg_validate(uid, 'delivery.guide', guide_id, 'guide_done', cr) 
	vals = {'printed':True} 
	pooler.get_pool(cr.dbname).get('delivery.guide').write(cr, uid, [guide_id], vals) 

#Guia de Despacho
def _guide(self, cr, uid, data, context):
	global list_print_file
	if not data:
		return {'resultado':"No hay datos...!"}	
	form = data['form']
	#Se obtiene el nombre de la  impresora
	printer_obj	=  pooler.get_pool(cr.dbname).get('ir.printers').read(cr, uid, form['printer'], ['printer'])

	if form['facturas']:
		#Consultar las Facturas de la Guia
		sql = """ 
		SELECT g.invoice_id  
		FROM   delivery_guide_line AS g  
		INNER JOIN  account_invoice AS a ON g.invoice_id=a.id  
		WHERE  g.guide_id=%d AND a.printed=False ;"""%form['guide'] 
		cr.execute (sql)
		result = cr.fetchall()
		for i in result:
			factura = i[0] 
			_invoice_print(cr, uid, factura, printer_obj['printer'])  
    
	#Imprimir Guia
	_guide_print(self, cr, uid, form['guide'],printer_obj['printer'])

	return {'resultado':"OK...!"}
		
class guide_prints(wizard.interface):
	
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form', 'arch' : datos_form, 'fields' : datos_fields, 'state' : [('end', 'Cancel'),('report', 'Imprimir') ]}
		},
		'report' :  {
			'actions' : [_guide],
			'result': {'type':'form', 'arch': result_form, 'fields': result_fields, 'state':[('end','OK')]}
		},		
	}

guide_prints("guide_invoice_print")
