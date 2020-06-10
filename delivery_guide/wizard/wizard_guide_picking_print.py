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

#Inicializacion de Variebles Globales------------------------------------------------------------------------------------------------
list_print_file = []

#Formulario del Wizard - Datos Entrada-----------------------------------------------------------------------------------------------
datos_form = '''<?xml version="1.0"?>
<form string="Imprimir Guia Traspasos">
	<separator colspan="2" string="Indique los Datos"/>
	<newline/>
	<field name="printer"/>
	<field name="guide"/>

</form>'''

datos_fields = {
	'printer': {'string':'Impresora', 'type':'many2one','relation': 'ir.printers', 'required':True,  'size':90 },
	'guide': {'string':'Guia Nro.', 'type':'many2one','relation': 'delivery.guide', 'required':True,  'size':90,  'domain':[('traspaso','=',1)] }
}


#Formulario del Wizard - Datos Salida------------------------------------------------------------------------------------------------
result_form = '''<?xml version="1.0"?>
<form string="Informacion">
	<field name="resultado"/>
</form>''' 

result_fields = {
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


#Obtener total Cajas por Factura ---------------------------------------------------------------------------------------------------------
def _get_cajas(cr, picking_id):
        cajas = '0'
        sql = "SELECT SUM(product_qty) as cajas FROM  stock_move WHERE picking_id=%d;"%picking_id
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
	fguia		= datosguia.date_guide
	transpor	= datosguia.carrier_company_id.name
	chofer		= datosguia.driver_id.name
	ruta		= datosguia.ruta_id.name
	almacen		= datosguia.warehouse_id.name
	#Validaciones Datos
	if datosguia.vehiculo_id.placa:
	    placa	= datosguia.vehiculo_id.placa

	#CREANDO ARCHIVO GUIA==========================================================================
	fileguia	= dir+'g'+nroguia+'.txt'
	output 	= codecs.open(fileguia,"w", "utf-8")
	#print "FG",fileguia
	#Datos Generales	
	output.write(" \n")
	output.write(" \n")
	output.write(" \n")
	output.write(boldon + normal + 'GUIA DE DESPACHO\n'.rjust(79))
	output.write(' '.rjust(64) + nroguia.center(15) + boldoff +'\n')
	output.write(" \n")
	output.write(" \n")
	output.write('TRANSPORTE: ' + transpor.ljust(45) + 'FECHA GUIA : ' + fguia +'\n')	
	output.write('CHOFER    : ' + chofer.ljust(45) + 'FECHA CARGA: __________\n')
	output.write('PLACA NRO.: ' + placa.ljust(45) + 'RUTA: ' + ruta +'\n')	
	output.write('ALMACEN   : ' + almacen.ljust(45) + 'DESTINO: __________\n')
	output.write(" \n")
	output.write(normal+"-------------------------------------------------------------------------------\n")	
	output.write(normal+'TRASPASO     ALMACEN DESTINO                                            CAJAS\n')
	output.write(normal+"-------------------------------------------------------------------------------\n")
	
	#Facturas de la Guia
	contf = 0
	totalcontado = 0
	totalcredito = 0
	totalcajas = 0	
	for picking in datosguia.guide_picking:
		nrof		= picking.picking_id.name
		almacen		= picking.picking_id.warehouse_dest_id.name
		contf 		+= 1
		cajas        = _get_cajas(cr,picking.picking_id.id)
		if cajas:
		    totalcajas += cajas
		cajas = locale.format('%.0f',  cajas, grouping=True)
		output.write(normal + nrof.ljust(10) +  almacen.center(20) + cajas.rjust(48) + '\n')

	#Productos de las Facturas de la Guia	
	output.write(" \n")
	#Total Faturas
	totalcajas = locale.format('%.0f',  totalcajas, grouping=True)
	output.write(comprime + ' '.ljust(60) + normal +  'TOTALES========>'.center(19) + ' '.rjust(21) + totalcajas.rjust(8) + '\n')
	output.write(" \t\n")	
	output.write(normal+"-------------------------------------------------------------------------------\n")	
	output.write(normal+'CODIGO   DESCRIPCION  PRODUCTO                           REFERENCIA     CAJAS\n')
	output.write(normal+"-------------------------------------------------------------------------------\n")

	totalcajas	= 0
	totalpeso	= 0
	contp		= 0
	pag         = 1
	sqlp = """
	SELECT  p.default_code,s.product_code,t.name,p.variants,SUM(m.product_qty) AS cantidad,t.weight_net  
	FROM	delivery_guide_picking_line    	 AS d
	INNER  JOIN stock_move AS m	 ON d.picking_id=m.picking_id
	INNER  JOIN product_product 	 AS p	 ON m.product_id=p.id
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
			ref = product[3].center(8)
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
		    while saltosln < 8:
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
	output.write(" \t\n")
	output.write(" \t\n")
	output.write('Total Cajas  ==================>> '.ljust(65) + 	totalcajas.rjust(11) +'\n')
	output.write('Total Peso   ==================>> '.ljust(65) + 	totalpeso.rjust(11) +'\n')		
	
	#Saltos de Linea -----------------------------------------------------------------------------------------------------------
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

#Guia de Despacho 
def _guide(self, cr, uid, data, context):
	global list_print_file
	if not data:
		return {'resultado':"No hay datos...!"}	
	form = data['form']
	#Se obtiene el nombre de la  impresora
	printer_obj	=  pooler.get_pool(cr.dbname).get('ir.printers').read(cr, uid, form['printer'], ['printer'])
    
	#Imprimir Guia
	_guide_print(self, cr, uid, form['guide'],printer_obj['printer'])
  
	return {'resultado':"OK...!"}
		
class guide_prints_picking(wizard.interface):
	
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

guide_prints_picking("guide_picking_print")
