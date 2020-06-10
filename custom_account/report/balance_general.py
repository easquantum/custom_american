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

class balance(report_sxw.rml_parse):
    ttsaldoant = 0
    ttsaldoact = 0
    ttbalance  = 0

    def __init__(self, cr, uid, name, context):
        super(balance, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'locale': locale, 
            'get_today': self._get_today,
            'get_move_lines': self._get_move_lines,
            'get_ttsaldoant': self._get_ttsaldoant,
            'get_ttsaldoact': self._get_ttsaldoact,
            'get_ttbalance': self._get_ttbalance,
        })
    
    def _get_today(self):
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        return today 

    def _get_ttsaldoant(self):
        return self.ttsaldoant

    def _get_ttsaldoact(self):
        return self.ttsaldoact

    def _get_ttbalance(self):
        return self.ttbalance

    def _get_move_lines(self,frm):
        numlevel  = int(frm['num_level'])
        account_id = frm['acc_id']
        fdesde = frm['date1']
        fhasta = frm['date2']
        filtro = "'1.%'"  
        move_lines=[]
        acclines  = []
        sqld = """ 
        SELECT g.id,g.code,SUM(g.saldo_ant) AS anterior,SUM(g.saldo_act) AS actual
        FROM(
                SELECT 
                a.id,a.code,COALESCE(0) AS saldo_ant,SUM(l.debit) - SUM(l.credit) AS saldo_act
                FROM account_account AS a 
                INNER JOIN account_move_line AS l ON a.id=l.account_id 
                WHERE  a.code  SIMILAR TO %s AND date BETWEEN   '%s' AND '%s' 
                GROUP BY a.id,a.code
                UNION  SELECT 
                a.id,a.code, SUM(l.debit) - SUM(l.credit) AS saldo_ant,COALESCE(0) AS saldo_act 
                FROM account_move_line AS l 
                LEFT JOIN account_account AS a ON a.id=l.account_id
                WHERE  a.code  SIMILAR TO %s AND date >= '2011-01-01' AND date < '%s' 
                GROUP BY a.id,a.code
        ) AS g
        GROUP BY g.id,g.code
        ORDER BY g.code desc
        """%(filtro,fdesde,fhasta,filtro,fdesde)
        #print sqld
        self.cr.execute (sqld)
        listd = self.cr.fetchall()
        #ACTIVOS
        sql	= """
        SELECT id,parent_id,code, name
        FROM account_account 
        WHERE active=True AND code SIMILAR TO '1.%'
        ORDER BY code
        """
        self.cr.execute (sql)
        list_acc = self.cr.fetchall()
        for l in list_acc:
            acc_level = 0
            saldo_ant = 0
            saldo_act = 0
            saldo     = 0
            acclines.append({'id':l[0],'parent':l[1],'code':l[2],'descrip':l[3],'anterior':saldo_ant,'actual':saldo_act,'saldo':saldo})
        total_activo_ant = 0
        total_activo_act = 0
        total_activo_bal = 0
        for l in listd:
            account_id = l[0]
            total_activo_ant += l[2]
            total_activo_act += l[3]
            total_activo_bal = total_activo_ant + total_activo_act
            while account_id:
                cont   = 0
                tt_ant = 0
                tt_act = 0
                tt_sld = 0
                enc    = False
                for ln in acclines:
                    if account_id == ln['id']:
                        tt_ant = acclines[cont]['anterior'] + l[2]
                        tt_act = acclines[cont]['actual']   + l[3]
                        tt_sld = tt_ant + tt_act
                        acclines[cont]['anterior'] = tt_ant
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
            code = l['code'].split('.')
            cuenta = l['descrip']
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
                move_lines.append({'code':l['code'],'descrip':cuenta,'anterior':l['anterior'],'actual':l['actual'],'saldo':l['saldo'],'space':space})

        #TOTAL ACTIVOS
        self.ttsaldoant = total_activo_ant
        self.ttsaldoact = total_activo_act
        self.ttbalance  = total_activo_bal
        #PASIVOS
        filtro = "'2.%'"
        sqldp = """ 
        SELECT g.id,g.code,SUM(g.saldo_ant) AS anterior,SUM(g.saldo_act) AS actual
        FROM(
                SELECT 
                a.id,a.code,COALESCE(0) AS saldo_ant,SUM(l.debit) - SUM(l.credit) AS saldo_act
                FROM account_account AS a 
                INNER JOIN account_move_line AS l ON a.id=l.account_id 
                WHERE  a.code  SIMILAR TO %s AND date BETWEEN   '%s' AND '%s' 
                GROUP BY a.id,a.code
                UNION  SELECT 
                a.id,a.code,SUM(l.debit) - SUM(l.credit) AS saldo_ant,COALESCE(0) AS saldo_act 
                FROM account_move_line AS l 
                LEFT JOIN account_account AS a ON a.id=l.account_id
                WHERE  a.code  SIMILAR TO %s AND date >= '2011-01-01' AND date < '%s' 
                GROUP BY a.id,a.code
        ) AS g
        GROUP BY g.id,g.code
        ORDER BY g.code desc
        """%(filtro,fdesde,fhasta,filtro,fdesde)
        self.cr.execute (sqldp)
        listdp = self.cr.fetchall()
        acclines=[]
        sqlp	= """
        SELECT id,parent_id,code, name
        FROM account_account 
        WHERE active=True AND code SIMILAR TO '2.%'
        ORDER BY code
        """
        self.cr.execute (sqlp)
        list_accp = self.cr.fetchall()
        for l in list_accp:
            acc_level = 0
            saldo_ant = 0
            saldo_act = 0
            saldo     = 0
            acclines.append({'id':l[0],'parent':l[1],'code':l[2],'descrip':l[3],'anterior':saldo_ant,'actual':saldo_act,'saldo':saldo})
        total_pasivo_ant = 0
        total_pasivo_act = 0
        total_pasivo_bal = 0
        for l in listdp:
            account_id = l[0]
            total_pasivo_ant += l[2]
            total_pasivo_act += l[3]
            total_pasivo_bal = total_pasivo_ant + total_pasivo_act
            while account_id:
                cont   = 0
                tt_ant = 0
                tt_act = 0
                tt_sld = 0
                enc    = False
                for ln in acclines:
                    if account_id == ln['id']:
                        tt_ant = acclines[cont]['anterior'] + l[2]
                        tt_act = acclines[cont]['actual']   + l[3]
                        tt_sld = tt_ant + tt_act
                        acclines[cont]['anterior'] = tt_ant
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
            code = l['code'].split('.')
            cuenta = l['descrip']
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
                move_lines.append({'code':l['code'],'descrip':cuenta,'anterior':l['anterior'],'actual':l['actual'],'saldo':l['saldo'],'space':space})

        #TOTAL PASIVOS
        if total_pasivo_ant < 0:
            self.ttsaldoant += total_pasivo_ant
        else: 
            self.ttsaldoant -= total_pasivo_ant
        if total_pasivo_act < 0:
            self.ttsaldoact += total_pasivo_act
        else:
            self.ttsaldoact -= total_pasivo_act
        if total_pasivo_bal < 0:
            self.ttbalance  += total_pasivo_bal
        else:
            self.ttbalance  -= total_pasivo_bal

        #CAPITAL
        filtro = "'3.%'"
        sqldc = """ 
        SELECT g.id,g.code,SUM(g.saldo_ant) AS anterior,SUM(g.saldo_act) AS actual
        FROM(
                SELECT 
                a.id,a.code,COALESCE(0) AS saldo_ant,SUM(l.debit) - SUM(l.credit) AS saldo_act
                FROM account_account AS a 
                INNER JOIN account_move_line AS l ON a.id=l.account_id 
                WHERE  a.code  SIMILAR TO %s AND date BETWEEN   '%s' AND '%s' 
                GROUP BY a.id,a.code
                UNION  SELECT 
                a.id,a.code,SUM(l.debit) - SUM(l.credit) AS saldo_ant,COALESCE(0) AS saldo_act 
                FROM account_move_line AS l 
                LEFT JOIN account_account AS a ON a.id=l.account_id
                WHERE  a.code  SIMILAR TO %s AND date >= '2011-01-01' AND date < '%s' 
                GROUP BY a.id,a.code
        ) AS g
        GROUP BY g.id,g.code
        ORDER BY g.code desc
        """%(filtro,fdesde,fhasta,filtro,fdesde)
        self.cr.execute (sqldc)
        listdc = self.cr.fetchall()
        acclines=[]
        sqlc	= """
        SELECT id,parent_id,code, name
        FROM account_account 
        WHERE active=True AND code SIMILAR TO '3.%'
        ORDER BY code
        """
        self.cr.execute (sqlc)
        list_accp = self.cr.fetchall()
        for l in list_accp:
            acc_level = 0
            saldo_ant = 0
            saldo_act = 0
            saldo     = 0
            acclines.append({'id':l[0],'parent':l[1],'code':l[2],'descrip':l[3],'anterior':saldo_ant,'actual':saldo_act,'saldo':saldo})
        total_cap_ant = 0
        total_cap_act = 0
        total_cap_bal = 0
        for l in listdc:
            account_id = l[0]
            total_cap_ant += l[2]
            total_cap_act += l[3]
            total_cap_bal = total_cap_ant + total_cap_act
            while account_id:
                cont   = 0
                tt_ant = 0
                tt_act = 0
                tt_sld = 0
                enc    = False
                for ln in acclines:
                    if account_id == ln['id']:
                        tt_ant = acclines[cont]['anterior'] + l[2]
                        tt_act = acclines[cont]['actual']   + l[3]
                        tt_sld = tt_ant + tt_act
                        acclines[cont]['anterior'] = tt_ant
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

        #Super Avit
        total_superavit_mes = 0
        total_superavit_ant = 0
        filtro = "'(4|8).%'"
        sqla	= """
        SELECT COALESCE(SUM(g.saldo_ant),0) AS anterior,COALESCE(SUM(g.saldo_act),0) AS actual
        FROM(
                SELECT COALESCE(0) AS saldo_ant,SUM(l.debit) - SUM(l.credit) AS saldo_act
                FROM account_account AS a 
                INNER JOIN account_move_line AS l ON a.id=l.account_id 
                WHERE  a.code  SIMILAR TO %s AND date BETWEEN   '%s' AND '%s' 
                UNION  SELECT 
                SUM(l.debit) - SUM(l.credit) AS saldo_ant,COALESCE(0) AS saldo_act 
                FROM account_move_line AS l 
                LEFT JOIN account_account AS a ON a.id=l.account_id
                WHERE  a.code  SIMILAR TO %s AND date >= '2011-01-01' AND date < '%s' 
        ) AS g
        """%(filtro,fdesde,fhasta,filtro,fdesde)
        #print sqla  
        self.cr.execute (sqla)
        result_a = self.cr.fetchall()
        if result_a and result_a[0]:
            total_superavit_ant = result_a[0][0]
            total_superavit_mes = result_a[0][1]
        
        filtro = "'(5|6|7|9).%'"
        sqlb	= """
        SELECT COALESCE(SUM(g.saldo_ant),0) AS anterior,COALESCE(SUM(g.saldo_act),0) AS actual
        FROM(
                SELECT COALESCE(0) AS saldo_ant,SUM(l.debit) - SUM(l.credit) AS saldo_act
                FROM account_account AS a 
                INNER JOIN account_move_line AS l ON a.id=l.account_id 
                WHERE  a.code  SIMILAR TO %s AND date BETWEEN   '%s' AND '%s' 
                UNION  SELECT 
                SUM(l.debit) - SUM(l.credit) AS saldo_ant,COALESCE(0) AS saldo_act 
                FROM account_move_line AS l 
                LEFT JOIN account_account AS a ON a.id=l.account_id
                WHERE  a.code  SIMILAR TO %s AND date >= '2011-01-01' AND date < '%s' 
        ) AS g
        """%(filtro,fdesde,fhasta,filtro,fdesde)
        #print sqlb 
        self.cr.execute (sqlb)
        result_b = self.cr.fetchall()
        if result_b and result_b[0]:
            total_superavit_ant += result_b[0][0]
            total_superavit_mes += result_b[0][1]
        total_cap_ant += total_superavit_ant
        total_cap_act += total_superavit_mes
        total_cap_bal = total_cap_ant + total_cap_act
        if total_superavit_ant or total_superavit_mes:
            account_id = frm['acc_id']
            while account_id:
                cont   = 0
                tt_ant = 0
                tt_act = 0
                tt_sld = 0
                enc    = False
                for ln in acclines:
                    if account_id == ln['id']:
                        tt_ant = acclines[cont]['anterior'] + total_superavit_ant
                        tt_act = acclines[cont]['actual']   + total_superavit_mes
                        tt_sld = tt_ant + tt_act
                        acclines[cont]['anterior'] = tt_ant
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
            code = l['code'].split('.')
            cuenta = l['descrip']
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
                move_lines.append({'code':l['code'],'descrip':cuenta,'anterior':l['anterior'],'actual':l['actual'],'saldo':l['saldo'],'space':space})
        #TOTAL CAPITAL
        if total_cap_ant < 0:
            self.ttsaldoant += total_cap_ant
        else: 
            self.ttsaldoant -= total_cap_ant
        if total_cap_act < 0:
            self.ttsaldoact += total_cap_act
        else:
            self.ttsaldoact -= total_cap_act
        if total_cap_bal < 0:
            self.ttbalance  += total_cap_bal
        else:
            self.ttbalance  -= total_cap_bal

        return move_lines 

report_sxw.report_sxw('report.balance_general','account.move','addons/custom_american/custom_account/report/balance_general.rml',parser=balance, header=False)