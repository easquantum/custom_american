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
import re

class declaracion_islr(report_sxw.rml_parse):
    #Variables Globales----------------------------------------------------
    ttbase	= 0
    ttgral	= 0
    #--------------------------------------------------------------------------
    def __init__(self, cr, uid, name, context):
        super(declaracion_islr, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_lines_islr': self._get_lines_islr, 
            'get_total_islr': self._get_total_islr,
            'get_company':self._get_company,
            'get_periodo': self._get_periodo,
            'get_ut': self._get_ut,
        })

    def _get_total_islr(self): 
        return self.ttgral

    #_crear_archivo-------------------------------------------------------------------------------------------
    # Se usa para crear el archivo en formato CSV
    #
    def _create_file_islr_csv(self,lns,fecha):
        #ruta = "/home/public/" # Desarrollo
        ruta = "/opt/openerp/reportes/compras/SENIAT/" # Server
        f= fecha.split('-')
        periodo = f[0] + f[1]
        rif     = self._get_company()
        rif     = rif.replace('-','')
        meses	= (['01','ENE'],['02','FEB'],['03','MAR'],['04','ABR'],['05','MAY'],['06','JUN'],['07','JUL'],['08','AGO'],['09','SEP'],['10','OCT'],['11','NOV'],['12','DIC'])
        a		= fecha[:4]
        m		= fecha[5:7]
        for x in meses:
            if x[0] == m:
                m	= x[1]
                break
        nb		= "ISLR-"+m+a+".csv"
        saltoln	= chr(13)+chr(10)
        filename= ruta+nb
        ln = 'Nro. ID;'+'Nro. Rif;'+'Nro. Fact;'+'Nro. Control;'+'Fecha Operacion;'+'Concepto;'+'Monto;'+'Porcentaje'
        output	= open(filename,"w")
        output.write(ln+saltoln)
        for ln in lns:
            ct = str(ln['cont'])
            rf = ln['rif']
            nf = ln['nrofac']
            nc = ln['nrocont']
            fo = ln['fecha']
            cd = ln['codigo']
            mt = ln['base']
            pr = ln['ret']
            mnt = locale.format('%.2f',  mt, grouping=True)
            mnt =	mnt.replace(',','.')
            prt   = locale.format('%.2f',  pr, grouping=True)
            prt   =	prt.replace(',','.')
            newln = ct+';'+rf+';'+nf+';'+nc+';'+fo+';'+cd+';'+mnt+';'+prt+'; '
            output.write(newln+saltoln)
        output.close()


    #_crear_archivo-------------------------------------------------------------------------------------------
    # Se usa para crear el archivo en formato XML
    #
    def _create_file_islr(self,lns,fecha):
        #ruta = "/home/public/" # Desarrollo
        ruta = "/opt/openerp/reportes/compras/SENIAT/" # Server
        f= fecha.split('-')
        periodo = f[0] + f[1]
        rif     = self._get_company()
        rif     = rif.replace('-','')
        meses	= (['01','ENE'],['02','FEB'],['03','MAR'],['04','ABR'],['05','MAY'],['06','JUN'],['07','JUL'],['08','AGO'],['09','SEP'],['10','OCT'],['11','NOV'],['12','DIC'])
        a		= fecha[:4]
        m		= fecha[5:7]
        for x in meses:
            if x[0] == m:
                m	= x[1]
                break
        nb		= "ISLR-"+m+a+".xml"
        saltoln	= chr(13)+chr(10)
        filename= ruta+nb
        output	= open(filename,"w")
        output.write('<?xml version="1.0" encoding="ISO-8859-1"?>'+saltoln)
        output.write('<RelacionRetencionesISLR RifAgente="'+rif+'" Periodo="'+periodo+'">'+saltoln)
        for ln in lns:
            fact  = ln['nrofac']
            contr = ln['nrocont']
            monto = locale.format('%.2f',  ln['base'], grouping=True)
            monto =	monto.replace(',','.')
            ret   = locale.format('%.2f',  ln['ret'], grouping=True)
            ret   =	ret.replace(',','.')
            output.write('<DetalleRetencion>'+saltoln)
            output.write('<RifRetenido>'+ln['rif']+'</RifRetenido>'+saltoln)
            output.write('<NumeroFactura>'+fact+'</NumeroFactura>'+saltoln)
            output.write('<NumeroControl>'+contr+'</NumeroControl>'+saltoln)
            output.write('<CodigoConcepto>'+ln['codigo']+'</CodigoConcepto>'+saltoln)
            output.write('<MontoOperacion>'+monto+'</MontoOperacion>'+saltoln)
            output.write('<PorcentajeRetencion>'+ret+'</PorcentajeRetencion>'+saltoln) 
            output.write('</DetalleRetencion>'+saltoln)
        output.write('</RelacionRetencionesISLR>')
        output.close()


    def _get_lines_islr(self,frm):
        result = []
        obj_islr = pooler.get_pool(self.cr.dbname).get('account.islr.tax')
        desde  = frm['date1']
        hasta  = frm['date2']
        tipo   =  "'"+frm['type_p']+"'"
        if frm['type_p'] == 'todo':
            tipo = "'natural','legal'" 
        self.ttgral = 0
        sql = """
        SELECT rp.vat,tt.code,it.amount_islr,it.porcentaje,it.id,it.base,it.document_date  
        FROM account_islr_tax                AS it  
        INNER JOIN res_partner               AS rp ON  it.partner_id=rp.id
        INNER JOIN account_islr_tax_type     AS tt ON  it.islr_type_id=tt.id 
        INNER JOIN account_islr_person_type  AS pt ON  tt.person_type_id=pt.id 
        WHERE it.state='done' AND pt.type in (%s) AND it.document_date BETWEEN '%s' AND '%s'
        ORDER BY tt.code,rp.vat;"""%(tipo,desde,hasta) 
        self.cr.execute (sql)
        datosislr = self.cr.fetchall()
        if not datosislr:
            result = [{'cont':'','rif':'','nrofac':'','nrocont':'','fecha':'','codigo':'','monto':0,'ret':0,'base':0}]
        cont   = 0
        total  = 0
        for datos in datosislr:
            cont  += 1
            rif    = datos[0]
            codigo = datos[1]
            total  = datos[2]
            porc   = datos[3]
            islr_id= datos[4]
            base   = datos[5]
            f      = datos[6]
            a      = f[:4]
            m      = f[5:7]
            d      = f[8:10]
            fecha = d+'/'+m+'/'+a
            nrfact = '0'
            nrcont = 'NA'
            self.ttgral += total
            islr = obj_islr.browse(self.cr, self.uid, islr_id)
            if islr.islr_line:
                nrfact = islr.islr_line[0].invoice_id.number_document
                if nrfact:
                    nrfact = nrfact.replace('-','') 
                    nrfact = re.sub("[^0-9]","", nrfact)
                if len(nrfact) > 8:
                    nrfact = nrfact[-8:]
                if nrfact:
                    nrfact = nrfact.zfill(8)
                nrcont = islr.islr_line[0].invoice_id.number_control
                if nrcont:
                    nrcont = nrcont.replace('-','')
                    nrcont = re.sub("[^0-9]","", nrcont)
                if nrcont and  len(nrcont) > 8:
                    nrcont = nrcont[-8:]
                if nrcont:
                    nrcont = nrcont.zfill(8)
            result.append({'cont':cont,'rif':rif,'nrofac':nrfact,'nrocont':nrcont,'fecha':fecha,'codigo':codigo,'monto':total,'ret':porc,'base':base}) 
        if frm['crearcsv']:
            rsp = self._create_file_islr_csv(result,hasta)
        if frm['crear']:
            rsp = self._create_file_islr(result,hasta)
        return result



    def _get_company(self):
        sql = " SELECT p.vat FROM res_company AS c  INNER JOIN res_partner AS p ON  c.partner_id=p.id;" 
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        company = ''
        if datos and datos[0] and datos[0][0]:
            company = datos[0][0]
        return company
    
    def _get_ut(self):
        ut = 0
        sql = " SELECT unit_tributaria FROM account_islr_tax_type WHERE unit_tributaria > 0;" 
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        if datos and datos[0] and datos[0][0]:
            ut = datos[0][0]
        return ut

    def _get_periodo(self,fecha):
        f= fecha.split('-')
        periodo = f[0] + f[1]	
        return periodo
		
report_sxw.report_sxw('report.declaracion_islr','account.islr.tax','addons/custom_american/islr/report/report_declaracion_islr.rml',parser=declaracion_islr, header=False)
