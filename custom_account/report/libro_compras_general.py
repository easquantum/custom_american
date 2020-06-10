# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007  Corvus Latinoamerica
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
import codecs

class libro_compras(report_sxw.rml_parse):
    ttcompra	= 0
    ttivaret	= 0
    ttbase		= 0
    ttiva		= 0
    ttexento	= 0
    ttncexento	= 0
    datostax	= []
    datosnctax	= []
    def __init__(self, cr, uid, name, context):
        super(libro_compras, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_today': self._get_today,
            'procesar_datos': self._procesar_datos,
            'get_libro_compras': self._get_libro_compras,
            'get_company':self._get_company,
            '_set_datos_tax': self._set_datos_tax,
            'get_totalgral_compra': self._get_totalgral_compra,
            'get_totalgral_exento': self._get_totalgral_exento,
            'get_totalgralnc_exento': self._get_totalgralnc_exento,
            'get_totalgral_base': self._get_totalgral_base,
            'get_totalgral_iva': self._get_totalgral_iva,
            'get_totalgral_ivaret': self._get_totalgral_ivaret,
            'get_datos_tax': self._get_datos_tax,
            'get_datos_nctax': self._get_datos_nctax,
        })

    #_set_datos_tax-------------------------------------------------------------------------------------------
    # Se usa para agrupar en un diccionario los diferentes tipos de impuestos
    #
    def _set_datos_tax(self,base,alicuota,iva,ivaret,tipo):
        cont_tax	= -1
        totaltax	= 0
        totalbase	= 0
        totalret	= 0
        newtax		= True
        datos       = []
        if tipo == 'NC':
            datos = self.datosnctax
        else:
            datos = self.datostax 
        if not datos:
            datos	= [{'tax':alicuota,'totaltax':iva,'totalbase':base,'totalret':ivaret}]
        else:
            for t in datos:
                cont_tax += 1
                totaltax	= t['totaltax']
                totalbase	= t['totalbase']
                totalret	= t['totalret']
                if alicuota == t['tax']:
                    newtax = False
                    break
            if newtax:
                datos.append({'tax':alicuota,'totaltax':iva,'totalbase':base,'totalret':ivaret})
            else:
                datos[cont_tax]['totaltax']	    = totaltax  + iva
                datos[cont_tax]['totalbase']	= totalbase + base
                datos[cont_tax]['totalret']	    = totalret  + ivaret
        return datos

    #_procesar_datos-------------------------------------------------------------------------------------------
    #Procesar datos del listado de facturas y Notas Credito de las compras administrativas y de Gestion
    #
    def _procesar_datos(self,listado):	
        libroCompras	= []
        self.datostax	= []
        self.datosnctax	= []
        cont			= 0
        obj_invoice = pooler.get_pool(self.cr.dbname).get('account.invoice')
        for ids in listado:
            #inicializacion de variables Locales----------------------------------------------------------------------------------------
            base		= 0
            iva			= 0
            ivaret		= 0
            totoal		= 0
            exento		= 0 
            alicuota	= 0
            tipodoc		= 'CO'
            nrofa       = ''
            exentas     = True
            invoice_id	= ids[0]
            invoices    = obj_invoice.browse(self.cr, self.uid, invoice_id)
            fecha       = invoices.date_document                     #Fecha del Documento [FACT - ND]			
            nrodoc		= invoices.number_document                   #Nro de FACT - ND
            nrocont		= invoices.number_control                    #Nro de Control
            rifp		= invoices.partner_id.vat                    #RIF Proveedor 
            porc_ret	= invoices.p_ret                             #Porcentaje Retencion
            amountotal	= invoices.amount_total                      #Total
            partner_id	= invoices.partner_id.id                     #ID Proveedor
            razonsocial	= invoices.partner_id.name                   #Razon Social invoices.address_invoice_id.name
            parent_id   = invoices.parent_id.id
            if invoices.amount_tax:
                #Consulta de impuesto y/o descuentos--------------------------------------------------------------------
                tax_ids 	= pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice_id) ])
                result_tax 	= pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr,self.uid, tax_ids,['name', 'base','amount'])
                #Productos EXENTOS-------------------------------------------------------------------------------------
                sqlsin="""
				SELECT SUM(a.price_unit * a.quantity) AS total
				FROM account_invoice_line AS a
				WHERE invoice_id=%d  AND a.id
				NOT IN (SELECT t.invoice_line_id  FROM  account_invoice_line_tax AS t 	WHERE a.id = t.invoice_line_id);"""%invoice_id
                self.cr.execute (sqlsin)
                rslt = self.cr.fetchall()
                if rslt[0][0]:
                    exento			=  rslt[0][0]
                    self.ttexento	+= exento
                    if invoices.type == 'in_refund':
                        self.ttncexento	+= exento
                for tax in result_tax:
                    #Se consulta el Grupo o tipo de Tax------------------------------------------------------------------
                    #los impuestos correspondientes al IVA, deben pertenecer al tipo 'vat'
                    #para poder ser procesados correctamente, de lo contraio seran descartados
                    tax_id		= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
                    tax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])
                    #Procesar FACTURAS CON  IMPUESTOS--------------------------------------------------------------------					
                    if tax_info[0]['tax_group'] == 'vat':
                        exentas = False
                        ivaret      = 0
                        alicuota	= tax_info[0]['amount'] * 100
                        iva			= tax['amount']
                        base		= tax['base']
                        total		= base + iva + exento
                        if porc_ret > 0:
                            ivaret = iva * porc_ret / 100
                        if invoices.type == 'in_refund':
                            self.ttcompra	 -= total
                            self.ttbase		 -= base
                            self.ttiva		 -= iva
                            self.ttivaret    -= ivaret
                            tipodoc  = 'NC'
                            self.datosnctax = self._set_datos_tax(base,alicuota,iva,ivaret,'NC')
                            fact_id 	= pooler.get_pool(self.cr.dbname).get('account.invoice').search(self.cr, self.uid, [('id','=',parent_id) ])
                            if fact_id:
                                fact_info	= pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, fact_id,['number_document'])
                                if fact_info and fact_info[0]:
                                    nrofa = fact_info[0]['number_document']
                        else:
                            self.ttcompra	 += total
                            self.ttbase		 += base
                            self.ttiva		 += iva
                            self.ttivaret    += ivaret
                            self.datostax = self._set_datos_tax(base,alicuota,iva,ivaret,'FA')
                        cont += 1
                        libroCompras.append({"cont":cont,"fecha":fecha, "rif": rifp, "proveedor":razonsocial, 'tipo':tipodoc, "nrodoc":nrodoc, "nrocont":nrocont ,"afect":nrofa, 'total':total, 'exento':exento, 'base':base, 'alicuota':alicuota, 'iva':iva, 'ivaret':ivaret})


            #Procesar Facturas o Notas Credito Exentas------------------------------------------------------------------
            if exentas:
                exento   = amountotal
                total    = amountotal
                cont     += 1
                if invoices.type == 'in_refund':
                    tipodoc  = 'NC'
                    if invoices.parent_id.id and invoices.parent_id.number_document:
                        nrofa    = invoices.parent_id.number_document
                    self.ttexento	-= exento
                    self.ttcompra	-= total
                    self.ttncexento	+= exento
                else:
                    self.ttexento	+= exento
                    self.ttcompra	+= total 
                libroCompras.append({"cont":cont,"fecha":fecha, "rif": rifp, "proveedor":razonsocial, 'tipo':tipodoc, "nrodoc":nrodoc, "nrocont":nrocont ,"afect":nrofa, 'total':total, 'exento':exento, 'base':base, 'alicuota':alicuota, 'iva':iva, 'ivaret':ivaret})

        return libroCompras

    #_set_format_num-------------------------------------------------------------------------------------------
    # Se usa para formatear los montos
    #
    def _set_format_num(self,num):
        #Validar
        if num:
            numf =	locale.format('%.2f',  num, grouping=True)
        else:
            numf = '0,00'
        return numf

    #_crear_archivo-------------------------------------------------------------------------------------------
    # Se usa para crear el archivo en formato CSV, con los datos del libro de ventas
    #
    def _crear_archivo(self, libro,fecha):
        #ruta = "/home/public/" # Desarrollo
        ruta = "/opt/openerp/reportes/librocompras/" # Server
        meses	= (['01','ENE'],['02','FEB'],['03','MAR'],['04','ABR'],['05','MAY'],['06','JUN'],['07','JUL'],['08','AGO'],['09','SEP'],['10','OCT'],['11','NOV'],['12','DIC'])
        a		= fecha[:4]
        m		= fecha[5:7]
        for x in meses:
            if x[0] == m:
                m	= x[1]
                break
        nb		= "LibroCompras-"+m+a+".csv"
        filename	= ruta+nb
        output	= codecs.open(filename,"w", "utf-8")
        ln = 'Nro.;'+'Fecha;'+'Nro. Rif;'+'Razon Social;'+'Tipo Doc.;'+'Nro. Fact N/C N/D;'+'Factura Afectada;'+'Nro. Control;'+'Total Compra incluye iva;'+'Compra sin Derecho Credito iva;'+'Base Imponible;'+'Alicuota;'+'IVA;'+'I.V.A Retenido'+'\t\n'
        output.write(ln)
        for l in libro:
            #Inicializando Variables del archivo-------------------------------------------------------------
            cnt = ' '   #Contador
            fc  = ' '   #Fecha
            rf  = ' '   #RIF
            rs  = ' '   #Razon Social
            tp  = ' '   #Tipo Documento
            doc = ' '   #Nro Documento
            fa  = ' '   #Nro Factura Afectada
            nc  = ' '   #Nro Control
            tc  = ' '   #Total Compra
            ex  = ' '   #Monto Exento
            tb  = ' '   #Monto Base
            al  = ' '   #Alicuota
            iv  = ' '   #IVA
            re  = ' '   #Iva Retenido
            #Asignado y Validando Valores--------------------------------------------------------------------
            cnt = str(l['cont'])
            if l['fecha']:
                fc = l['fecha']
            if l['rif']:
                rf = l['rif']
            if l['proveedor']:
                rs = l['proveedor']
            if l['tipo']:
                tp = l['tipo']
            if l['nrodoc']:
                doc = l['nrodoc']
            if l['afect']:
                fa = l['afect'] 
            if l['nrocont']:
                nc = l['nrocont']
            tc  = self._set_format_num(l['total'])
            ex  = self._set_format_num(l['exento'])
            tb  = self._set_format_num(l['base'])
            iv  = self._set_format_num(l['iva'])
            re  = self._set_format_num(l['ivaret'])
            al  = self._set_format_num(l['alicuota'])
            ln = cnt+';'+fc+';'+rf+';'+rs+';'+tp+';'+doc+';'+fa+';'+nc+';'+tc+';'+ex+';'+tb+';'+al+';'+iv+';'+re+'; \t\n'
            output.write(ln)
        output.close()
        return

    def _get_libro_compras(self, form):
        #inicializacion de variables Globale------------------------------------------------------------------------------------------
        self.ttcompra   = 0
        self.ttivaret   = 0
        self.ttbase     = 0
        self.ttiva      = 0
        self.ttexento   = 0
        self.ttncexento	= 0
        self.datostax	= []
        self.datosnctax	= []
        #inicializacion de variables Locales------------------------------------------------------------------------------------------		
        datoslibro		= []
        fdesde			= form['date1']
        fhasta			= form['date2']
        filtro		= "'in_refund','"+form['filtro']+"'"
        if form['filtro'] == 'todo':
            filtro = "'in_invoice','in_invoice_ad','in_refund'"
        #Datos  
        sql = """
        SELECT  a.id  
        FROM 	  account_invoice AS a 
        WHERE  a.type in (%s) AND a.internal=False AND a.check=False AND a.adjustment=False AND a.state in ('open','paid') AND a.date_invoice BETWEEN '%s' AND '%s'  
        ORDER BY a.date_document;"""%(filtro,fdesde,fhasta)	
        #print sql 
        self.cr.execute (sql)
        listado = self.cr.fetchall()
        if listado:
            datoslibro = self._procesar_datos(listado)
        else:
            return [{'cont':'','fecha':'', 'rif':'', 'proveedor':'','tipo':'', 'nrodoc':'','nrocont':'','afect':'','total':0,'exento':0,'base':0,'alicuota':0,'iva':0,'ivaret':0}]
        #Creado archivo 
        rsp = self._crear_archivo(datoslibro,fhasta)
        return datoslibro

    def _get_today(self):
        today = datetime.datetime.now().strftime("%d-%m-%y %I:%M") 
        return today

    def _get_company(self):
        sql		= "SELECT c.name, p.vat, p.nit FROM res_company AS c INNER JOIN  res_partner AS p ON c.partner_id=p.id	 WHERE c.id=1" 
        self.cr.execute (sql)
        datos_company = self.cr.fetchall()
        company			= datos_company[0]
        return company

    def _get_totalgral_compra(self): 
        return self.ttcompra

    def _get_totalgral_exento(self):
        return self.ttexento

    def _get_totalgralnc_exento(self):
        return self.ttncexento

    def _get_totalgral_base(self): 
        return self.ttbase
    
    def _get_totalgral_iva(self): 
        return self.ttiva
    
    def _get_totalgral_ivaret(self): 
        return self.ttivaret

    def _get_datos_tax(self):
        return self.datostax
    
    def _get_datos_nctax(self):
        return self.datosnctax

report_sxw.report_sxw('report.libro_compras_gral','account.invoice','addons/custom_american/custom_account/report/libro_compras_general.rml',parser=libro_compras, header=False)
