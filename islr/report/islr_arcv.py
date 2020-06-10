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

class arcv(report_sxw.rml_parse):
    rif        = ''
    rifp       = ''
    comp_tipo  = ''
    comp_tlf  = ''
    part_tipo  = ''
    comp_dir   = ''
    part_dir   = ''
    part_tlf   = ''
    tttipo     = 0
    ttbasegral = 0
    ttretgral  = 0
    dat_arcv = []

    def __init__(self, cr, uid, name, context):
        super(arcv, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale, 
            'get_today': self._get_today,
            'get_company':self._get_company,
            'get_company_address':self._get_company_address,
            'get_tlf_company':self._get_tlf_company,
            'get_rif_company':self._get_rif_company,
            'get_tipo_company':self._get_tipo_company,
            'get_partner':self._get_partner,
            'get_partner_address':self._get_partner_address,
            'get_tlf_partner':self._get_tlf_partner,
            'get_rif_partner':self._get_rif_partner,
            'get_tipo_partner':self._get_tipo_partner,
            'get_invoice': self._get_invoice,
            'get_detalle': self._get_detalle,
            'get_totalbase': self._get_totalbase,
            'get_totalret': self._get_totalret,
            'set_totales': self._set_totales,
            'get_mes': self._get_mes,
            'get_arcv': self._get_arcv,
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today

    def _get_mes(self,m):
        meses	= (['01','ENERO'],['02','FEBRERO'],['03','MARZO'],['04','ABRIL'],['05','MAYO'],['06','JUNIO'],['07','JULIO'],['08','AGOSTO'],['09','SEPTIEMBRE'],['10','OCTUBRE'],['11','NOVIEMBRE'],['12','DICIEMBRE'])
        mes     = ''
        for x in meses:
            if x[0] == m:
                mes	= x[1]
        return mes

    def _set_totales(self,mes,ttb,ttr,ttba,ttra,porc):
        cnt = 0
        for m in self.dat_arcv:
            if m['mes'] == mes:
                self.dat_arcv[cnt]['totalf']    = ttb
                self.dat_arcv[cnt]['ttbase']    = ttb
                self.dat_arcv[cnt]['ttret']     = ttr
                self.dat_arcv[cnt]['ttacumb']   = ttba
                self.dat_arcv[cnt]['ttacumret'] = ttra
                self.dat_arcv[cnt]['porc'] = porc
                self.dat_arcv[cnt]['set'] = True
                break
            cnt += 1
        return

    def _get_detalle(self,frm):
        self.dat_arcv = []
        ttbase = 0
        ttret  = 0
        cont   = 0
        mes    = '01'
        self.dat_arcv.append({'mes':'ENERO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'FEBRERO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'MARZO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'ABRIL','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'MAYO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'JUNIO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'JULIO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'AGOSTO','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'SEPTIEMBRE','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'OCTUBRE','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'NOVIEMBRE','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.dat_arcv.append({'mes':'DICIEMBRE','totalf':0,'ttbase':0,'porc':0,'ttret':0,'ttacumb':0,'ttacumret':0,'set':False})
        self.ttbasegral = 0
        self.ttretgral  = 0
        type_tmp = 0
        desde  = frm['date1']
        hasta  = frm['date2']
        partner_id = frm['supplierid']
        sql = """
        SELECT id,document_date,base,porcentaje,amount_islr 
        FROM account_islr_tax 
        WHERE state != 'cancel' AND partner_id=%d AND document_date BETWEEN '%s' AND '%s'
        ORDER BY document_date,porcentaje"""%(partner_id,desde,hasta)
        #print sql
        self.cr.execute (sql)
        datosislr = self.cr.fetchall()

        for d in datosislr:
            fecha = d[1]
            m     = fecha[5:7]
            cont   += 1
            if m != mes and cont == 1:
                mes    = m

            if m != mes:
                ttb = locale.format('%.2f',  ttbase, grouping=True, monetary=True)
                ttr = locale.format('%.2f',  ttret, grouping=True, monetary=True)
                ttba= locale.format('%.2f',  self.ttbasegral, grouping=True, monetary=True)
                ttra= locale.format('%.2f',  self.ttretgral, grouping=True, monetary=True)
                nbmes = self._get_mes(mes)
                self._set_totales(nbmes,ttb,ttr,ttba,ttra,porc)
                ttbase = 0
                ttret  = 0
                mes    = m
                    
            #Se obtienen los datos de la factura si existen--------------------------------------------------
            ttbase += d[2]
            ttret  += d[4]
            porc    = d[3]
            islr_id = d[0]
            self.ttbasegral += d[2]
            self.ttretgral  += d[4]
            #invoices = self._get_invoice(islr_id)
        #Totales
        ttb = locale.format('%.2f',  ttbase, grouping=True, monetary=True)
        ttr = locale.format('%.2f',  ttret, grouping=True, monetary=True)
        ttba= locale.format('%.2f',  self.ttbasegral, grouping=True, monetary=True)
        ttra= locale.format('%.2f',  self.ttretgral, grouping=True, monetary=True)
        nbmes = self._get_mes(mes)
        self._set_totales(nbmes,ttb,ttr,ttba,ttra,porc)
        return 

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

    def _get_company(self): 
        sql="""
        SELECT c.name,p.vat,t.name 
        FROM res_company AS c  
        INNER JOIN res_partner AS p ON  c.partner_id=p.id 
        LEFT JOIN account_islr_person_type AS t ON  p.person_type_id=t.id;
        """ 
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        self.rif = ''
        self.comp_tipo = ''
        nomb     = ''
        if datos and datos[0] and datos[0][0]:
            nomb = datos[0][0]
        if datos and datos[0] and datos[0][1]:
            self.rif = datos[0][1]
        if datos and datos[0] and datos[0][2]:
            self.comp_tipo = datos[0][2]
        return nomb

    def _get_company_address(self): 
        sql="""
        SELECT d.street,d.street2,d.phone  
        FROM res_company AS c  
        INNER JOIN res_partner AS p ON  c.partner_id=p.id
        INNER JOIN res_partner_address AS d ON p.id=d.partner_id;"""
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        dir     = ''
        self.comp_tlf  = ''
        if datos and datos[0] and datos[0][0]:
            dir = datos[0][0]
        if datos and datos[0] and datos[0][1]:
            dir += '  '+datos[0][1]
        if datos and datos[0] and datos[0][2]:
            self.comp_tlf  = datos[0][2]
        return dir

    def _get_tlf_company(self):
        return self.comp_tlf

    def _get_tlf_company(self):
        return self.comp_tlf

    def _get_partner_address(self,partner_id): 
        sql="""
        SELECT street,street2,phone 
        FROM res_partner_address
        WHERE partner_id=%d AND type='default';"""%partner_id 
        self.cr.execute (sql)
        datp_address = self.cr.fetchall()
        dir     = ''
        self.part_tlf = ''
        if datp_address and datp_address[0] and datp_address[0][0]:
            dir = datp_address[0][0]
        if datp_address and datp_address[0] and datp_address[0][1]:
            dir += '  '+datp_address[0][1]
        if datp_address and datp_address[0] and datp_address[0][2]:
            self.part_tlf = datp_address[0][2]
        return dir

    def _get_tlf_partner(self):
        return self.part_tlf

    def _get_rif_company(self):
        return self.rif

    def _get_tipo_company(self):
        return self.comp_tipo

    def _get_partner(self,partner_id): 
        sql="""SELECT p.name,p.vat,t.name  
        FROM res_partner AS p  
        INNER JOIN res_partner_address AS a ON  a.partner_id=p.id 
        LEFT JOIN account_islr_person_type AS t ON  p.person_type_id=t.id
        WHERE p.id=%d;"""%partner_id
        self.cr.execute (sql)
        datos = self.cr.fetchall()
        self.rifp = ''
        nomb     = ''
        if datos and datos[0] and datos[0][0]:
            nomb = datos[0][0]
        if datos and datos[0] and datos[0][1]:
            self.rifp = datos[0][1]
        if datos and datos[0] and datos[0][2]:
            self.part_tipo = datos[0][2]
        return nomb

    def _get_rif_partner(self):
        return self.rifp

    def _get_tipo_partner(self):
        return self.part_tipo

    def _get_arcv(self):
        cnt = 0 
        antb = 0
        antret = 0
        for d in self.dat_arcv:
            if d['set'] == True:
                antb = d['ttacumb']
                antret = d['ttacumret']
            if d['set'] == False:
                self.dat_arcv[cnt]['ttacumb']   = antb
                self.dat_arcv[cnt]['ttacumret'] = antret
            cnt += 1 
        return self.dat_arcv 

    def _get_totalbase(self):
        totalgral = locale.format('%.2f',  self.ttbasegral, grouping=True, monetary=True)
        return totalgral

    def _get_totalret(self):
        totalgral = locale.format('%.2f',  self.ttretgral, grouping=True, monetary=True)
        return totalgral

report_sxw.report_sxw('report.islr_arcv','account.islr.tax','addons/custom_american/islr/report/islr_arcv.rml',parser=arcv, header=False)
