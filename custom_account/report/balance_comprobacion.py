# -*- encoding: utf-8 -*-
########################################################################################################
#
# Copyright (c) 2007 - 2013 Corvus Latinoamerica, C.A. (http://corvus.com.ve) All Rights Reserved
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

class comprobacion(report_sxw.rml_parse):
    ttdebe  = 0
    tthaber = 0

    def __init__(self, cr, uid, name, context):
        super(comprobacion, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale, 
            'get_today': self._get_today,
            'get_move_lines': self._get_move_lines,
            'get_total_debe': self._get_total_debe,
            'get_total_haber': self._get_total_haber,
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today 

    def _get_move_lines(self,frm):
        numlevel   = int(frm['num_level'])
        fdesde     = frm['date1']
        fhasta     = frm['date2']
        accounts   = int(frm['accounts'])
        move_lines = []
        acclines   = []
        self.ttdebe = 0
        self.tthaber= 0
        sqld = """ 
        SELECT 
        g.id,
        g.code,
        SUM(g.saldo_ant) AS anterior,
        SUM(g.saldo_debe) AS debe,
        SUM(g.saldo_haber) AS haber,
        SUM(g.saldo_act) AS actual
        FROM(
                SELECT 
                a.id,
                a.code,
                COALESCE(0) AS saldo_ant,
                SUM(l.debit) AS saldo_debe,
                SUM(l.credit) AS saldo_haber,
                SUM(l.debit) - SUM(l.credit) AS saldo_act
                FROM       account_account   AS a 
                INNER JOIN account_move_line AS l ON a.id=l.account_id 
                WHERE date BETWEEN   '%s' AND '%s' 
                GROUP BY a.id,a.code
                UNION  SELECT 
                a.id,
                a.code, 
                SUM(l.debit) - SUM(l.credit) AS saldo_ant,
                COALESCE(0) AS saldo_debe,
                COALESCE(0) AS saldo_haber,
                COALESCE(0) AS saldo_act 
                FROM      account_move_line AS l 
                LEFT JOIN account_account   AS a ON a.id=l.account_id
                WHERE  date >= '2011-01-01' AND date < '%s' 
                GROUP BY a.id,a.code
        ) AS g
        GROUP BY g.id,g.code
        ORDER BY g.code desc
        """%(fdesde,fhasta,fdesde)
        #print sqld
        self.cr.execute (sqld)
        listd = self.cr.fetchall()
        #Codigo Contable
        sql	= """
        SELECT id,parent_id,code, name
        FROM account_account 
        WHERE active=True AND code!='0'
        ORDER BY code
        """
        self.cr.execute (sql)
        list_acc = self.cr.fetchall()
        for l in list_acc:
            acclines.append({'id':l[0],'parent':l[1],'code':l[2],'descrip':l[3],'anterior':0,'debe':0,'haber':0,'actual':0,'saldo':0})

        for l in listd:
            account_id = l[0]
            self.ttdebe  += l[3]
            self.tthaber += l[4]
            while account_id:
                cont   = 0
                tt_ant = 0
                tt_deb = 0
                tt_cre = 0
                tt_act = 0
                tt_sld = 0
                enc    = False
                for ln in acclines:
                    if account_id == ln['id']:
                        tt_ant = acclines[cont]['anterior'] + l[2]
                        tt_deb = acclines[cont]['debe']     + l[3]
                        tt_cre = acclines[cont]['haber']    + l[4]
                        tt_act = acclines[cont]['actual']   + l[5]
                        tt_sld = tt_ant + tt_act
                        acclines[cont]['anterior'] = tt_ant
                        acclines[cont]['debe']     = tt_deb
                        acclines[cont]['haber']    = tt_cre
                        acclines[cont]['actual']   = tt_act
                        acclines[cont]['saldo']    = tt_sld
                        if account_id != acclines[cont]['parent']:
                            account_id = acclines[cont]['parent']
                        else:
                            account_id = 0
                        enc        = True
                        break 
                    cont +=1
                if not enc:
                    account_id = 0

        for l in acclines:
            space      = ''
            acc_level  = 0
            code       = l['code'].split('.')
            cuenta     = l['descrip']
            saldo  = l['saldo']
            actual = l['actual']
            if int(code[5]):
                acc_level = 6
                space      = '...............'
            elif int(code[4]):
                acc_level = 5
                space      = '............'
            elif int(code[3]):
                acc_level = 4
                space      = '.........'
            elif int(code[2]):
                acc_level = 3
                space      = '......'
            elif int(code[1]):
                acc_level = 2
                space      = '...'
            elif int(code[0]):
                acc_level = 1
                cuenta = l['descrip'].upper()
            if acc_level <= numlevel:
                if accounts==1:
                    move_lines.append({'code':l['code'],'descrip':cuenta,'saldoant':l['anterior'],'debe':l['debe'],'haber':l['haber'],'saldomes':l['actual'],'saldo':l['saldo'],'space':space})
                elif accounts==2 and saldo:
                    move_lines.append({'code':l['code'],'descrip':cuenta,'saldoant':l['anterior'],'debe':l['debe'],'haber':l['haber'],'saldomes':l['actual'],'saldo':l['saldo'],'space':space})
                elif accounts==3 and actual:
                    move_lines.append({'code':l['code'],'descrip':cuenta,'saldoant':l['anterior'],'debe':l['debe'],'haber':l['haber'],'saldomes':l['actual'],'saldo':l['saldo'],'space':space})
        return move_lines 

    def _get_total_debe(self): 
        return self.ttdebe

    def _get_total_haber(self):
        return self.tthaber

report_sxw.report_sxw('report.balance_comprobacion','account.move','addons/custom_american/custom_account/report/balance_comprobacion.rml',parser=comprobacion, header=False)
