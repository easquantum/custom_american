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


#SELECT  i.id,i.name,i.quantity,i.price_unit,t.name,t.amount,t.tax_group, i.quantity * i.price_unit * t.amount  AS impuesto
#FROM account_invoice_line AS i
#INNER JOIN account_invoice_line_tax AS l ON i.id=l.invoice_line_id
#INNER JOIN account_tax AS t ON l.tax_id=t.id
#WHERE invoice_id=403
#GROUP BY i.id,i.name,i.quantity,i.price_unit,t.name,t.amount,t.tax_group,t.sequence
#order by i.name,t.sequence


import time
import datetime
import locale
from report import report_sxw
from osv import osv
import pooler

class retentionsbysupplier_ret(report_sxw.rml_parse):
    #Inicializacion de Variables Globales--------------------------------------------------------------------
    ttimpuesto    = 0
    ttretencion    = 0
    ttbase        = 0
    ttiva        = 0
    ttotal        = 0
    ttotalsin    = 0
    
    def __init__(self, cr, uid, name, context):
        super(retentionsbysupplier_ret, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale,
            'get_today': self._get_today,
            'get_periodo':self._get_periodo,
            'get_detalle': self._get_detalle,
            'get_cod_retenc': self._get_cod_retenc,
            'get_address_company':self._get_address_company,
            'get_razon_partner':self._get_razon_partner,
            'get_mes': self._get_mes,    
            'get_totalgral_base': self._get_totalgral_base,        
            'get_totalgral_iva': self._get_totalgral_iva,
            'get_totalgral_rec': self._get_totalgral_rec,
            'get_totalgral_con': self._get_totalgral_con,    
            'get_totalgral_sin': self._get_totalgral_sin,
            'get_supplierid': self._get_supplierid,
            'get_final_date': self._get_final_date,
        })
  
    
    def _get_final_date(self,data):
        return self.pool.get('account.retention').read(self.cr, self.uid, data['id'], ['final_date'])['final_date']
    
    def _get_supplierid(self,data):
        return self.pool.get('account.retention').read(self.cr, self.uid, data['id'], ['partner_id'])['partner_id']

    def _get_detalle(self,retencion_id):
        datos = []
        cont = 0
        obj_retencion = pooler.get_pool(self.cr.dbname).get('account.retention')
        datosret = obj_retencion.browse(self.cr, self.uid, retencion_id)
        if not datosret.retention_line:
            return [{"item":'',"fecha": '',"tipo":'', "nrofact":'',"nrocont":'',"notac":'',"afectada":'',"totalconiva":0,"totalsin":0,"base":0,"alicuota":0,"iva":0,"ivaret":0}]
        for invoice in datosret.retention_line:
            #Inicializacion de Variables---------------------------------------------------------------------------------------------- 
            base       = 0
            iva        = 0
            retenc     = 0
            alicuota   = 0
            total      = 0    
            totalsin   = 0 
            fecha      = invoice.invoice_id.date_document
            nrofact    = invoice.invoice_id.number_document
            nrocont    = invoice.invoice_id.number_control
            notad      = ''
            notac      = ''
            afectada   = ''
            tipodoc    = 'C'
            if invoice.invoice_id.type == 'in_refund':
                tipodoc = 'NC'
                notac   = nrofact
                nrofact = ''
                fact    = pooler.get_pool(self.cr.dbname).get('account.invoice').read(self.cr, self.uid, invoice.invoice_id.parent_id.id,['number_document'])
                afectada = fact['number_document'] 
            cont        += 1
            #Se consultan los Impuesto  -----------------------------------------------------------------------------------------------------------------
            tax_invoice_ids = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').search(self.cr, self.uid, [('invoice_id','=',invoice.invoice_id.id) ])
            resulttax       = pooler.get_pool(self.cr.dbname).get('account.invoice.tax').read(self.cr, self.uid, tax_invoice_ids,['name','base','amount'])
            if resulttax: 
                for tax in resulttax:
                    #Se Obtiene el Grupo o tipo de Tax-----------------------------------------------------------------------------
                    print tax['name']
                    tax_id      = pooler.get_pool(self.cr.dbname).get('account.tax').search(self.cr, self.uid, [('name','=',tax['name']) ])
                    tax_info    = pooler.get_pool(self.cr.dbname).get('account.tax').read(self.cr, self.uid, tax_id,['tax_group','amount'])
                    if tax_info and tax_info[0]['tax_group'] == 'vat':
                        alicuota    = tax_info[0]['amount'] * 100
                        iva         = tax['amount']
                        base        = tax['base']    
                        total       = base + iva
                        if invoice.invoice_id.p_ret > 0:
                            retenc = iva * invoice.invoice_id.p_ret / 100         
                #Consultar productos sin impuestos----------------------------------------------------------------------------------------
                sqlsin ="""
                SELECT SUM(a.price_unit * a.quantity) AS totalsin  
                FROM account_invoice_line AS a 
                WHERE invoice_id=%d  AND a.id 
                NOT IN (SELECT t.invoice_line_id FROM  account_invoice_line_tax AS t WHERE a.id = t.invoice_line_id) """%invoice.invoice_id.id
                self.cr.execute (sqlsin)
                dats = self.cr.fetchall()
                if dats[0][0]:
                    totalsin = dats[0][0]
                    total       += totalsin    

            datos.append({"item":cont, "fecha": fecha,"tipo":tipodoc, "nrofact":nrofact,"nrocont":nrocont,"notac":notac,"afectada":afectada,"totalconiva":total,"totalsin":totalsin,"base":base,"alicuota":alicuota,"iva":iva,"ivaret":retenc})
            #Totales-------------------------------------------------------------------------------------------------------------------
            if invoice.invoice_id.type == 'in_refund':
                base   *= -1
                iva    *= -1
                total  *= -1
                retenc *= -1
                totalsin *= -1
                            
            self.ttretencion    += retenc
            self.ttbase         += base
            self.ttiva          += iva    
            self.ttotal         += total
            self.ttotalsin      += totalsin         
        return datos

    def _get_address_company(self): 
        self.cr.execute (""" SELECT d.street,d.street2, d.phone 
                                                 FROM res_company AS c
                                                  INNER JOIN res_partner AS p ON  c.partner_id=p.id
                                                 INNER JOIN  res_partner_address AS d ON p.id=d.partner_id;""")
                                                 
        datos = self.cr.fetchall()
        dir = datos[0][0] + "  " + datos[0][1] + "    Telf: " + datos[0][2]
        return dir

    def _get_razon_partner(self,partner): 
        sql="""
        SELECT d.name 
        FROM  res_partner AS p  
        INNER JOIN  res_partner_address AS d ON p.id=d.partner_id
        WHERE p.id=%d AND d.type='default';"""%partner
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dir = datos[0][0]
        return dir
        
    def _get_mes(self,fecha):
        if fecha:
            f= fecha.split('-')
            m = {'mes':f[1]}    
            return m['mes']
        return ''

    def _get_periodo(self,fecha):
        if fecha:
            f= fecha.split('-')
            periodo = {'a':f[0],'m':f[1]}    
            return periodo
        return ''

    def _get_totalgral_base(self): 
        return self.ttbase        

    def _get_totalgral_iva(self): 
        return self.ttiva        
        
    def _get_totalgral_rec(self): 
        return self.ttretencion        

    def _get_totalgral_sin(self): 
        return self.ttotalsin
            
    def _get_totalgral_con(self): 
        return self.ttotal    
                        
    def _get_cod_retenc(self):
        info = self.pool.get('account.retention').read(self.cr, self.uid, self.localcontext['data']['id'], ['code','state'])
        if info['state'] == 'draft':
               return 'Borrador' 
        return info['code']
            
        
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today
                        
report_sxw.report_sxw('report.retenciones_por_proveedor_ret','account.retention','addons/retention/report/retenciones_por_proveedor_ret.rml',parser=retentionsbysupplier_ret, header=False)
