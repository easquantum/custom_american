# -*- encoding: utf-8 -*-
########################################################################################################
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
########################################################################################################

import time
import datetime
import locale
from report import report_sxw
from osv import osv
import pooler

class islr_det(report_sxw.rml_parse):
    rif        = ''
    tttipo     = 0
    ttbasegral = 0
    ttretgral  = 0

    def __init__(self, cr, uid, name, context):
        super(islr_det, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale, 
            'get_tipo': self._get_tipo,
            'get_today': self._get_today,
            'get_company':self._get_company,
            'get_rif_company':self._get_rif_company,
            'get_invoice': self._get_invoice,
            'get_detalle': self._get_detalle,
            'get_totalbase': self._get_totalbase,
            'get_totalret': self._get_totalret,
            'get_periodo': self._get_periodo,			
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today

    def _get_detalle(self,frm):
        result = []
        ttbase = 0
        ttret  = 0
        cont   = 0
        self.ttbasegral = 0
        self.ttretgral  = 0
        type_tmp = 0
        desde  = frm['date1']
        hasta  = frm['date2']
        sql = """
        SELECT it.id,tt.id,tt.name,tt.porcentaje,rp.name,rp.vat,it.base,it.amount_islr,tt.sustraendo,tt.code 
        FROM account_islr_tax AS it  
        INNER JOIN res_partner AS rp ON  it.partner_id=rp.id
        INNER JOIN account_islr_tax_type AS tt ON  it.islr_type_id=tt.id 
        WHERE it.document_date BETWEEN '%s' AND '%s'
        ORDER BY tt.code,rp.vat
        """%(desde,hasta)
        self.cr.execute (sql)
        datosislr = self.cr.fetchall()
        if not datosislr:
            result = [{'prov':'','rif':'','nrofac':'','nrocont':'','fecha':'','cheq':'','totalf':0,'base':0,'ret':0,'sust':'','codigo':''}]
        for d in datosislr:
            islr_id = d[0]
            type_id = d[1]
            nbi     = d[2]
            porc    = d[3]
            nbp     = d[4]
            rif     = d[5]
            base    = d[6]
            ret     = d[7]
            sustr   = d[8]
            cod     = d[9]
            cont   += 1
            ttbase += base
            ttret  += ret
            self.ttbasegral += base
            self.ttretgral  += ret
            if type_tmp !=type_id:
                if cont > 1:
                    ttbase -= base
                    ttret  -= ret
                    ttb = locale.format('%.2f',  ttbase, grouping=True, monetary=True)
                    ttr = locale.format('%.2f',  ttret, grouping=True, monetary=True)
                    result.append({'prov':'SUB-TOTAL','rif':'','nrofac':'','nrocont':'','fecha':'','cheq':'','totalf':'','base':ttb,'ret':ttr,'sust':'','codigo':''})
                    ttbase = base
                    ttret  = ret
                porc = locale.format('%.2f',  porc, grouping=True)
                nbi = nbi.upper()
                result.append({'prov':nbi,'rif':porc + '  %','nrofac':'','nrocont':'','fecha':'','cheq':'','totalf':'','base':'','ret':'','sust':'','codigo':''})
                type_tmp = type_id
            bs = locale.format('%.2f',  base, grouping=True, monetary=True)
            re = locale.format('%.2f',  ret, grouping=True, monetary=True)
            sustr = locale.format('%.2f',sustr, grouping=True, monetary=True)
            nbp = nbp.lower()
            #Se obtienen los datos de la factura si existen--------------------------------------------------
            invoices = self._get_invoice(islr_id)
            result.append({'prov':nbp,'rif':rif,'nrofac':invoices['nfact'],'nrocont':invoices['ncont'],'fecha':invoices['fecha'],'cheq':'','totalf':invoices['total'],'base':bs,'ret':re,'sust':sustr,'codigo':cod})
        #Totales
        ttb = locale.format('%.2f',  ttbase, grouping=True, monetary=True)
        ttr = locale.format('%.2f',  ttret, grouping=True, monetary=True)
        result.append({'prov':'SUB-TOTAL','rif':'','nrofac':'','nrocont':'','fecha':'','cheq':'','totalf':'','base':ttb,'ret':ttr,'sust':'','codigo':''})
        return result

    def _get_invoice(self,islr_id):
        datfact = {'nfact':'N/A','ncont':'N/A','fecha':'','total':0}
        obj_islr = pooler.get_pool(self.cr.dbname).get('account.islr.tax')
        islr     = obj_islr.browse(self.cr, self.uid, islr_id)
        total    = 0
        if islr.islr_line:
            datfact['nfact'] = islr.islr_line[0].invoice_id.number_document
            datfact['ncont'] = islr.islr_line[0].invoice_id.number_control
            fech = islr.islr_line[0].invoice_id.date_document
            if fech:
                datfact['fecha'] = time.strftime('%d/%m/%Y', time.strptime(fech, '%Y-%m-%d')) 
        for l in islr.islr_line:
            total += l.invoice_id.amount_total
        datfact['total'] = locale.format('%.2f',  total, grouping=True, monetary=True)
        return datfact

    def _get_tipo(self,type):
        tipo = ''
        if type and type == 'legal':
            tipo = 'Juridico'
        else:
            tipo = 'Natural'
        return tipo

    def _get_company(self): 
        sql="SELECT c.name,p.vat FROM res_company AS c  INNER JOIN res_partner AS p ON  c.partner_id=p.id;" 
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        self.rif = ''
        nomb     = ''
        if datos and datos[0] and datos[0][0]:
            nomb = datos[0][0]
        if datos and datos[0] and datos[0][1]:
            self.rif = datos[0][1]
        return nomb

    def _get_periodo(self,fecha):
        meses	= (['01','ENERO'],['02','FEBEBRO'],['03','MARZO'],['04','ABRIL'],['05','MAYO'],['06','JUNIO'],['07','JULIO'],['08','AGOSTO'],['09','SEPTIEMBRE'],['10','OCTUBRE'],['11','NOVIEMBRE'],['12','DICIEMBRE'])
        a		= fecha[:4]
        m		= fecha[5:7]
        m		= str(m)
        for x in meses:
            if x[0] == m:
                m	= x[1]
        periodo	= m+'  '+a
        return periodo

    def _get_rif_company(self):
        return self.rif

    def _get_totalbase(self):
        return self.ttbasegral

    def _get_totalret(self):
        return self.ttretgral

report_sxw.report_sxw('report.islr_resumen','account.islr.tax','addons/custom_american/islr/report/report_resumen_islr.rml',parser=islr_det, header=False)
