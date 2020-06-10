# -*- coding: utf-8 -*- 
##############################################################################
#
# Copyright (c) 2009 Corvus Latinoamerica
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
import codecs
import pooler
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from reportlab.lib import colors

class libro_ventas(report_sxw.rml_parse):
    #Variables Globales----------------------------------------------------
    ttventa		= 0
    ttexento	= 0
    ttivaret	= 0
    ttbase		= 0
    ttiva		= 0
    ttventanc	= 0
    ttexentonc	= 0
    ttbasenc	= 0
    ttivanc		= 0
    totalret_iva= 0
    totalret_iva_nc= 0
    ttbase_nocontribuyente		= 0
    ttiva_nocontribuyente		= 0
    datoslibros	= []
    datostax	= []
    datosnctax	= []
    lblank		= []
	
    def __init__(self, cr, uid, name, context):
        super(libro_ventas, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time': time,
                'locale': locale,
                'get_today': self._get_today,
                'validar_datos': self._validar_datos,
                'get_libro_ventas': self._get_libro_ventas,
                'get_totalgral_venta': self._get_totalgral_venta,
                'get_totalgral_exento': self._get_totalgral_exento,
                'get_totalgral_exento_nc': self._get_totalgral_exento_nc,
                'get_totalgral_base': self._get_totalgral_base,
                'get_base_nocontibuyente': self._get_base_nocontibuyente,
                'get_totalgral_base_nc': self._get_totalgral_base_nc,
                'get_totalgral_retencion': self._get_totalgral_retencion,
                'get_totalgral_iva': self._get_totalgral_iva,
                'get_iva_nocontibuyente': self._get_iva_nocontibuyente,
                'get_totalgral_iva_nc': self._get_totalgral_iva_nc,
                'get_company':self._get_company,
                'get_total_base_exento': self._get_total_base_exento,
                'get_periodo': self._get_periodo,
                'get_totalret_iva': self._get_totalret_iva,
                'get_totalret_iva_nc': self._get_totalret_iva_nc,
                'get_totalret_periodo': self._get_totalret_periodo,
                '_set_datos_tax': self._set_datos_tax,
                '_set_datos_tax_nc': self._set_datos_tax_nc,
                'get_datos_tax': self._get_datos_tax,
                'get_datos_tax_nc': self._get_datos_tax_nc,
                'set_format_num': self._set_format_num,
                'crear_archivo': self._crear_archivo,
            })
    #_set_datos_tax-------------------------------------------------------------------------------------------
    # Se usa para agrupar en un diccionario los diferentes tipos de impuestos
    #
    def _set_datos_tax(self,alicuota,iva,base):
        cont_tax	= -1
        totaltax	= 0
        totalbase	= 0
        totalret	= 0
        ivaret      = 0
        newtax		= True
        if not self.datostax:
            self.datostax	= [{'tax':alicuota,'totaltax':iva,'totalbase':base,'totalret':ivaret}]
        else:
            for t in self.datostax:
                cont_tax += 1
                totaltax	= t['totaltax']
                totalbase	= t['totalbase']
                totalret	= t['totalret']
                if alicuota == t['tax']:
                    newtax = False
                    break
            if newtax:
                self.datostax.append({'tax':alicuota,'totaltax':iva,'totalbase':base,'totalret':ivaret})
            else:
                self.datostax[cont_tax]['totaltax']	    = totaltax  + iva
                self.datostax[cont_tax]['totalbase']	= totalbase + base
                self.datostax[cont_tax]['totalret']	    = totalret  + ivaret
        return True

    #_set_datos_tax-------------------------------------------------------------------------------------------
    # Se usa para agrupar en un diccionario los diferentes tipos de impuestos de las notas creditos
    #
    def _set_datos_tax_nc(self,alicnc,ivanc,basenc):
        contnc_tax	= -1
        totaltaxnc	= 0
        totalbasenc	= 0
        totalretnc	= 0
        ivaretnc    = 0
        newtaxnc	= True
        if not self.datosnctax:
            self.datosnctax	= [{'tax':alicnc,'totaltax':ivanc,'totalbase':basenc,'totalret':0}]
        else:
            for tnc in self.datosnctax:
                contnc_tax += 1
                totaltaxnc	= tnc['totaltax']
                totalbasenc	= tnc['totalbase']
                totalretnc	= tnc['totalret']
                if alicnc == tnc['tax']:
                    newtaxnc = False
                    break
            if newtaxnc:
                self.datosnctax.append({'tax':alicnc,'totaltax':ivanc,'totalbase':basenc,'totalret':ivaretnc})
            else:
                self.datosnctax[contnc_tax]['totaltax']	  = totaltaxnc  + ivanc
                self.datosnctax[contnc_tax]['totalbase']  = totalbasenc + basenc
                self.datosnctax[contnc_tax]['totalret']	  = totalretnc  + ivaretnc
        return True


    def _validar_datos(self,listado):
        #Variables Globales----------------------------------------------------
        datoslibro		= []
        cont			= 0
        self.ttventa	= 0
        self.ttexento	= 0
        self.ttivaret	= 0
        self.ttbase		= 0
        self.ttiva		= 0
        self.ttventanc	= 0
        self.ttexentonc	= 0
        self.ttbasenc	= 0
        self.ttivanc	= 0 
        self.ttbase_nocontribuyente		= 0
        self.ttiva_nocontribuyente		= 0
        self.datostax	= []
        self.datosnctax = []
        for invoices in listado:
            #Variables Locales-------------------------------------------------------------------------------------------
            base		= 0
            iva			= 0
            ivaret		= 0
            totventa 	= 0
            exento		= 0
            alicuota	= 0
            nrofact     = ''
            nronotac    = ''
            tipodoc		= 'FA'
            invoice_id  = invoices[0]                #ID de la Factura
            finvoice	= invoices[1]                #Fecha Factura
            nrodoc		= invoices[2]                #Nro Documento [Factura - Nota Credito]
            nrocont	    = '' #invoices[]             #Nro Control NO APLICA por que no se registra en el sistema
            tipo		= invoices[3]                #Tipo Documento [out_invoice=Factura - out_refund=Nota Credito] 
            estatus		= invoices[4]                #Estatus del Documento [Open - Cancel]
            idcli		= invoices[7]                #ID Cliente
            rifprov		= invoices[8]                #RIF del Cliente
            razonsocial	= ''                         #Razon Social del Cliente
            monto       = invoices[5]                #Monto Factura
            nrocp		= ''                         #Nro de Comprobante
            nrofa       = ''                         #Nro Factura Afectada por una nota de credito
            not_contributor = invoices[10]           #No Contribuyente
            #Se Obtiene la Razon social
            address_ids  = pooler.get_pool(self.cr.dbname).get('res.partner.address').search(self.cr, self.uid, [('partner_id','=',idcli) ])
            if address_ids:
                address_info = pooler.get_pool(self.cr.dbname).get('res.partner.address').read(self.cr, self.uid, [address_ids[0]],['name'])
                if address_info and address_info[0] and address_info[0]['name']:
                    razonsocial	= address_info[0]['name'] 
            nrofact     = nrodoc
            if tipo == 'out_refund':
                tipodoc		= 'NC'
                nrofact     = ''
                nronotac    = nrodoc
                afectad_id  = invoices[9]           #Factura Afectada
                if afectad_id:
                    nfact = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, [afectad_id],['number'])
                    #if nfact and nfact[0]['number']:
                    nrofa = nfact[0]['number']    
            if estatus == 'cancel':
                tipodoc = 'AN'
                result_tax 	= []
                cont		+= 1
                datoslibro.append({'cont':cont,'fecha':finvoice, 'rif': rifprov, 'proveedor':razonsocial,'tipo':tipodoc,'nrofac':nrofact,"nrocont":nrocont,'nronotac':nronotac,'afect':nrofa,'total':totventa,'exento':exento,'base':base,'alicuota':alicuota,'iva':iva,'ivaret':ivaret,'nrocomp':nrocp})
            else:
                #Se consulta de impuesto y/o descuentos de la factura----------------------------------------------------
                tax_ids 	= pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice_id) ])
                result_tax 	= pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr,self.uid, tax_ids,['name', 'base','amount'])
                if not result_tax and monto: #Procesar FACTURAS SIN  IMPUESTOS-------------------------------------------
                    exento		 = monto
                    totventa 	 = monto
                    if tipo == 'out_invoice':
                        self.ttventa   += totventa
                        self.ttexento  += exento
                    else:
                        self.ttventa   -= totventa
                        self.ttexento  -= exento
                        self.ttventanc   += totventa
                        self.ttexentonc  += exento
                    cont		+= 1
                    datoslibro.append({'cont':cont,'fecha':finvoice, 'rif': rifprov, 'proveedor':razonsocial,'tipo':tipodoc,'nrofac':nrofact,"nrocont":nrocont,'nronotac':nronotac,'afect':nrofa,'total':totventa,'exento':exento,'base':base,'alicuota':alicuota,'iva':iva,'ivaret':ivaret,'nrocomp':nrocp})
                    exento		 = 0
                    totventa 	 = 0
                else:
                    #FACTURAS CON PRODUCTOS EXENTOS--------------
                    sqlsin ="""
					SELECT SUM(a.price_unit * a.quantity) AS totalsin
					FROM account_invoice_line AS a
					WHERE invoice_id=%d  AND a.id
					NOT IN (SELECT t.invoice_line_id FROM  account_invoice_line_tax AS t WHERE a.id = t.invoice_line_id);"""%invoice_id
                    self.cr.execute (sqlsin)
                    inf_exento = self.cr.fetchall()
                    if inf_exento[0][0]:
                        exento		= inf_exento[0][0]
                    solodescto = True
                    for tax in result_tax: #Procesar FACTURAS CON IMPUESTOS O DESCUENTOS--------------------------------- 
                        #Se obtiene el Grupo o tipo de Tax----------------------------------
                        tax_id	= pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
                        tax_info	= pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])
                        if tax_info and tax_info[0]['tax_group'] == 'vat':
                            solodescto  = False
                            alicuota	= tax_info[0]['amount'] * 100
                            base		= tax['base']
                            iva			= tax['amount']
                            totventa	= tax['base'] + tax['amount'] + exento
                            self.ttexento  += exento
                            cont	       += 1
                            if tipo == 'out_invoice':
                                self.ttbase		+= base
                                self.ttiva		+= iva
                                self.ttventa	+= totventa
                                self._set_datos_tax(alicuota,iva,base)
                                if not_contributor:
                                    self.ttbase_nocontribuyente		+= base
                                    self.ttiva_nocontribuyente		+= iva
                            else:
                                self.ttbase		-= base
                                self.ttiva		-= iva
                                self.ttventa	-= totventa
                                self.ttbasenc	+= base
                                self.ttivanc	+= iva
                                self.ttventanc  += totventa
                                self._set_datos_tax_nc(alicuota,iva,base)
                            datoslibro.append({'cont':cont,'fecha':finvoice, 'rif': rifprov, 'proveedor':razonsocial,'tipo':tipodoc,'nrofac':nrofact,"nrocont":nrocont,'nronotac':nronotac,'afect':nrofa,'total':totventa,'exento':exento,'base':base,'alicuota':alicuota,'iva':iva,'ivaret':ivaret,'nrocomp':nrocp}) 
                            exento = 0
                    if solodescto: 
                        exento		 = monto
                        totventa 	 = monto
                        if tipo == 'out_invoice':
                            self.ttventa   += totventa
                            self.ttexento  += exento
                        else:
                            self.ttventa   -= totventa
                            self.ttexento  -= exento
                        cont		+= 1
                        datoslibro.append({'cont':cont,'fecha':finvoice, 'rif': rifprov, 'proveedor':razonsocial,'tipo':tipodoc,'nrofac':nrofact,"nrocont":nrocont,'nronotac':nronotac,'afect':nrofa,'total':totventa,'exento':exento,'base':base,'alicuota':alicuota,'iva':iva,'ivaret':ivaret,'nrocomp':nrocp})
        #Variables Globales----------------------------------------------------
        #print "CONT",cont 
        return datoslibro

    #_set_format_num-------------------------------------------------------------------------------------------
    # Se usa para formatear los montos
    #
    def _set_format_num(self,num):
        if num:
            numf	=	locale.format('%.2f',  num, grouping=True)
            #numf	=	numf.replace(',','.')
        else:
            numf = '0,00'
        return numf  


    #_crear_archivo-------------------------------------------------------------------------------------------
    # Se usa para crear el archivo en formato CSV, con los datos del libro de ventas
    #
    def _crear_archivo(self, libro,fecha): 
        #Creando  Archivo Plano del SENIAT---------------
        #ruta = "/home/public/" # Desarrollo
        ruta = "/opt/openerp/reportes/libroventas/" # Server
        #Nombre del archivo-------------
        meses	= (['01','ENE'],['02','FEB'],['03','MAR'],['04','ABR'],['05','MAY'],['06','JUN'],['07','JUL'],['08','AGO'],['09','SEP'],['10','OCT'],['11','NOV'],['12','DIC'])
        a		= fecha[:4]
        m		= fecha[5:7]
        for x in meses:
            if x[0] == m:
                m	= x[1]
        nb		= "LibroVentas-"+m+a+".csv" 
        filename	= ruta+nb
        output	= codecs.open(filename,"w", "utf-8")
        ln = 'Fecha;'+'Rif;'+'Razon Social;'+'Nro. Comprobante;'+'Nro. Factura;'+'Nota Debito;'+'Nota Credito;'+'Tipo Doc;'+'Factura Afectada;'+'Total Venta con IVA;'+'Ventas No Gravadas;'+'Base Imponible;'+'Alicuota;'+'IVA'+ '\t\n'
        output.write(ln)
        for l in libro:
            #Inicializando Variables del archivo---------------------------------------------------------------
            fc   = ' '   #Fecha
            rf   = ' '   #RIF
            rs   = ' '   #Razon Social
            tp   = ' '   #Tipo Doc
            nf   = ' '   #Nro Factura
            nc   = ' '   #Nro Control
            ntd  = ' '   #Nota Debito
            ntc  = ' '   #Nota Credito
            fa   = ' '   #Factura Afectada
            tt   = 0     #Total Doc
            ex   = 0     #Monto Exento
            bs   = 0     #Monto Base
            iv   = 0     #Monto IVA
            al   = 0     #Alicuota
            ir   = 0     #Iva retenido
            ncp  = ' '   #Nro Comprobante
            #print "L",l
            #Asignando Variables------------------------------------------------------------------------------
            if l['fecha']:
                fc   = l['fecha']
            if l['rif']:
                rf   = l['rif']
            if l['proveedor']:
                rs   = l['proveedor']
            if l['tipo']:
                tp   = l['tipo']
            if l['nrofac']:
                nf   = l['nrofac']
            #ntd   = l['nronotad']
            if l['nronotac']:
                ntc  = l['nronotac']
            if l['afect']:
                fa   = l['afect']
            #ncp  = l['nrocomp']
            tt   = self._set_format_num(l['total']) 
            ex   = self._set_format_num(l['exento'])
            bs   = self._set_format_num(l['base'])
            iv   = self._set_format_num(l['iva'])
            al   = self._set_format_num(l['alicuota'])
            #ir   = self._set_format_num(l['ivaret'])
            ln = fc+';'+rf+';'+rs+';'+ncp+';'+nf+';'+ntd+';'+ntc+';'+tp+';'+fa+';'+tt+';'+ex+';'+bs+';'+al+';'+iv+ ';0\t\n'
            output.write(ln)        
        output.close()
        return


    def _get_libro_ventas(self, form):
        #inicializacion de variables------------------------------------------------------------------------------------
        libro_venta		= []
        self.ttcompra	= 0
        self.ttivaret	= 0
        self.ttbase		= 0
        self.ttiva		= 0
        fdesde		= form['date1']
        fhasta		= form['date2']
        #Consulta de las facturas del Periodo--------------------------------------------------------------------------- 
        sql = """
        SELECT a.id,a.date_invoice,a.name,a.type,a.state,a.amount_total,a.amount_tax,p.id,p.vat,a.parent_id,p.not_contributor      
        FROM   account_invoice AS a
        INNER  JOIN res_partner AS p ON a.partner_id=p.id 
        WHERE  a.adjustment=False AND a.state in ('draft','open','paid','cancel') AND a.type in ('out_invoice','out_refund') AND a.date_invoice BETWEEN '%s' AND '%s'
        ORDER  BY a.date_invoice;"""%(fdesde,fhasta)
        #print sql
        self.cr.execute (sql)
        listado = self.cr.fetchall()
        libro_venta = self._validar_datos(listado)
        x = self._crear_archivo(libro_venta,fhasta) 
        libro_venta		= [] 
        return libro_venta

    def _get_totalret_periodo(self,form):
        totalret_periodo = 0 
        self.totalret_iva = 0
        self.totalret_iva_nc = 0
        fdesde		= form['date1']
        fhasta		= form['date2']
        #Consulta Monto Retenido en Facturasdel Periodo-------------------------------------------- 
        sql = """
        SELECT  COALESCE(SUM(rl.retention_amount),0) AS retenido     
        FROM	account_invoice            AS ai
        INNER JOIN account_retention_line  AS rl ON ai.id=rl.invoice_id 
        INNER JOIN account_retention       AS rt ON rl.retention_id=rt.id 
        WHERE  rt.inicial_date BETWEEN '%s' AND '%s' AND ai.type = 'out_invoice' AND ai.adjustment=False 
        AND ai.state != 'cancel' 
        """%(fdesde,fhasta)
        #print sql
        self.cr.execute (sql)
        retenido_iva = self.cr.fetchall()
        if retenido_iva and retenido_iva[0]:
            self.totalret_iva = retenido_iva[0][0]

        
        #Consulta Monto Retenido en Facturasdel Periodo-------------------------------------------- 
        sql = """
        SELECT  COALESCE(SUM(rl.retention_amount),0) AS retenido     
        FROM	account_invoice            AS ai
        INNER JOIN account_retention_line  AS rl ON ai.id=rl.invoice_id 
        INNER JOIN account_retention       AS rt ON rl.retention_id=rt.id 
        WHERE  rt.inicial_date BETWEEN '%s' AND '%s' AND ai.type = 'out_refund' AND ai.adjustment=False 
        AND ai.state != 'cancel' 
        """%(fdesde,fhasta)
        #print sql
        self.cr.execute (sql)
        retenido_nc = self.cr.fetchall()
        if retenido_nc and retenido_nc[0]:
            self.totalret_iva_nc = retenido_nc[0][0]

        if self.totalret_iva:
            totalret_periodo = self.totalret_iva
        if self.totalret_iva_nc:
            totalret_periodo -= self.totalret_iva_nc
        return totalret_periodo

    def _get_totalret_iva(self):
        return self.totalret_iva

    def _get_totalret_iva_nc(self):
        return self.totalret_iva_nc

    def _get_totalgral_venta(self):
        return self.ttventa

    def _get_totalgral_base(self):
        return self.ttbase

    def _get_totalgral_iva(self):
        return self.ttiva

    def _get_base_nocontibuyente(self):
        return self.ttbase_nocontribuyente

    def _get_iva_nocontibuyente(self):
        return self.ttiva_nocontribuyente

    def _get_totalgral_retencion(self):
        return self.ttivaret

    def _get_totalgral_exento(self):
        return self.ttexento

    
    def _get_total_base_exento(self):
        total_base_exento = self.ttbase + self.ttexento
        return total_base_exento


    def _get_totalgral_exento_nc(self):
        return self.ttexentonc

    def _get_totalgral_base_nc(self):
        return self.ttbasenc

    def _get_totalgral_iva_nc(self):
        return self.ttivanc

    def _get_datos_tax(self,form):
        #Calculo de Retencion por Alicuota
        if self.datostax:
            cont = 0
            alc  = 0
            fdesde		= form['date1']
            fhasta		= form['date2']
            for t in self.datostax:
                retiva = 0
                if not t['tax']:
                    continue
                alc   = int(t['tax'])
                porc   = str(alc)
                proc   = porc.zfill(2)
                sql = """
                SELECT  COALESCE(SUM(rl.retention_amount),0) AS retenido 
                FROM account_retention_line        AS rl 
                INNER JOIN account_invoice         AS ai ON ai.id=rl.invoice_id 
                INNER JOIN account_retention       AS rt ON rl.retention_id=rt.id 
                INNER JOIN account_invoice_tax     AS it ON ai.id=it.invoice_id 
                INNER JOIN account_tax             AS at ON it.name=at.name
                WHERE  rt.inicial_date BETWEEN '%s' AND '%s' 
                AND ai.type = 'out_invoice' AND ai.adjustment=False AND ai.state != 'cancel' 
                AND at.tax_group='vat' AND at.amount='0.%s'
                """%(fdesde,fhasta,proc)
                #print sql
                self.cr.execute (sql)
                retenido = self.cr.fetchall()
                if retenido and retenido[0]:
                    retiva = retenido[0][0]
                    self.datostax[cont]['totalret'] = retiva
                cont += 1
                
        if not self.datostax:
            self.datostax	= [{'tax':'','totaltax':0,'totalbase':0,'totalret':0}]
        return self.datostax

    def _get_datos_tax_nc(self,form):
        #Calculo de Retencion por Alicuota
        if self.datosnctax:
            cont = 0
            alc  = 0
            fdesde		= form['date1']
            fhasta		= form['date2']
            for t in self.datosnctax:
                if not t['tax']:
                    continue
                retiva = 0
                alc   = int(t['tax'])
                porc   = str(alc)
                proc   = porc.zfill(2)
                sql = """
                SELECT  COALESCE(SUM(rl.retention_amount),0) AS retenido 
                FROM account_retention_line        AS rl 
                INNER JOIN account_invoice         AS ai ON ai.id=rl.invoice_id 
                INNER JOIN account_retention       AS rt ON rl.retention_id=rt.id 
                INNER JOIN account_invoice_tax     AS it ON ai.id=it.invoice_id 
                INNER JOIN account_tax             AS at ON it.name=at.name
                WHERE  rt.inicial_date BETWEEN '%s' AND '%s' 
                AND ai.type = 'out_refund' AND ai.adjustment=False AND ai.state != 'cancel' 
                AND at.tax_group='vat' AND at.amount='0.%s'
                """%(fdesde,fhasta,proc) 
                self.cr.execute (sql)
                retenido = self.cr.fetchall()
                if retenido and retenido[0]:
                    retiva = retenido[0][0]
                    self.datosnctax[cont]['totalret'] = retiva
                cont += 1
        if not self.datosnctax:
            self.datosnctax	= [{'tax':'','totaltax':0,'totalbase':0,'totalret':0}]
        return self.datosnctax

    def _get_company(self):
        sql		= "SELECT c.name, p.vat  FROM res_company AS c INNER JOIN  res_partner AS p ON c.partner_id=p.id	 WHERE c.id=1"
        self.cr.execute (sql)
        datos_company	= self.cr.fetchall()
        company		= datos_company[0]
        return company

    def _get_today(self):
        today = datetime.datetime.now().strftime("%d-%m-%y %I:%M")
        return today

    def _get_periodo(self,fecha):
        a		= fecha[:4]
        meses	= (['01','ENE'],['02','FEB'],['03','MAR'],['04','ABR'],['05','MAY'],['06','JUN'],['07','JUL'],['08','AGO'],['09','SEP'],['10','OCT'],['11','NOV'],['12','DIC'])
        mes		= fecha[5:7]
        mes		= str(mes)
        mes_periodo	= ''
        periodo	= ''
        for x in meses:
            if x[0] == mes:
                mes_periodo	= x[1]
        periodo = mes_periodo + ' - ' + str(a)
        return periodo
								
report_sxw.report_sxw('report.libro_ventas','account.invoice','addons/custom_american/custom_account/report/report_libro_ventas.rml',parser=libro_ventas, header=False)
