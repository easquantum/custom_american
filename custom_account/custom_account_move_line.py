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


from osv import fields,osv,orm
import pooler
import tools
from tools import config
import netsvc
from tools.translate import _
import time
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime


class res_partner(osv.osv):
    _inherit = "account.move.line" 
    _columns = {  
    
    }
    _defaults = { 
    
    }

    def reconcile(self, cr, uid, ids, type='auto', writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False, context={}):
        id_set = ','.join(map(str, ids))
        lines = self.browse(cr, uid, ids, context=context)
        unrec_lines = filter(lambda x: not x['reconcile_id'], lines)
        credit = debit = 0.0
        currency = 0.0
        account_id = False
        partner_id = False
        for line in unrec_lines:
            if line.state <> 'valid':
                raise osv.except_osv(_('Error'),_('Entry "%s" is not valid !') % line.name)
            credit += line['credit']
            debit += line['debit']
            currency += line['amount_currency'] or 0.0
            account_id = line['account_id']['id']
            partner_id = (line['partner_id'] and line['partner_id']['id']) or False
        writeoff = debit - credit
        # Ifdate_p in context => take this date
        if context.has_key('date_p') and context['date_p']:
            date=context['date_p']
        else:
            date = time.strftime('%Y-%m-%d')
        sqlmove = 'SELECT account_id, reconcile_id FROM account_move_line WHERE id IN ('+id_set+')  GROUP BY account_id,reconcile_id'
        cr.execute(sqlmove)
        r = cr.fetchall()
        #TODO: move this check to a constraint in the account_move_reconcile object
        if (len(r) != 1) and not context.get('fy_closing', False):
            raise osv.except_osv(_('Error'), _('Entries are not of the same account or already reconciled ! '))
        if not unrec_lines:
            raise osv.except_osv(_('Error'), _('Entry is already reconciled'))
        account = self.pool.get('account.account').browse(cr, uid, account_id, context=context)
        if not context.get('fy_closing', False) and not account.reconcile:
            raise osv.except_osv(_('Error'), _('The account is not defined to be reconcile !'))
        if r[0][1] != None:
            raise osv.except_osv(_('Error'), _('Some entries are already reconciled !'))

        if (not self.pool.get('res.currency').is_zero(cr, uid, account.company_id.currency_id, writeoff)) or (account.currency_id and (not self.pool.get('res.currency').is_zero(cr, uid, account.currency_id, currency))):
            if not writeoff_acc_id:
                raise osv.except_osv(_('Warning'), _('You have to provide an account for the write off entry !'))
            if writeoff > 0:
                debit = writeoff
                credit = 0.0
                self_credit = writeoff
                self_debit = 0.0
            else:
                debit = 0.0
                credit = -writeoff
                self_credit = 0.0
                self_debit = -writeoff
            # If comment exist in context, take it
            if 'comment' in context and context['comment']:
                libelle=context['comment']
            else:
                libelle='Write-Off'
            writeoff_lines = [
                (0, 0, {
                    'name':libelle,
                    'debit':self_debit,
                    'credit':self_credit,
                    'account_id':account_id,
                    'date':date,
                    'partner_id':partner_id,
                    'currency_id': account.currency_id.id or False,
                    'amount_currency': account.currency_id.id and -currency or 0.0
                }),
                (0, 0, {
                    'name':libelle,
                    'debit':debit,
                    'credit':credit,
                    'account_id':writeoff_acc_id,
                    'date':date,
                    'partner_id':partner_id
                })
            ]
            writeoff_move_id = self.pool.get('account.move').create(cr, uid, {
                'period_id': writeoff_period_id,
                'journal_id': writeoff_journal_id,
                'state': 'draft',
                'line_id': writeoff_lines
            })
            writeoff_line_ids = self.search(cr, uid, [('move_id', '=', writeoff_move_id), ('account_id', '=', account_id)])
            ids += writeoff_line_ids
        r_id = self.pool.get('account.move.reconcile').create(cr, uid, {
            #'name': date,
            'type': type,
            'line_id': map(lambda x: (4,x,False), ids),
            'line_partial_ids': map(lambda x: (3,x,False), ids)
        })
        wf_service = netsvc.LocalService("workflow")
        # the id of the move.reconcile is written in the move.line (self) by the create method above
        # because of the way the line_id are defined: (4, x, False)
        #print "IDS",ids
        for id in ids:
            #print "WRKFLOW",id,"UID",uid
            w = wf_service.trg_trigger(uid, 'account.move.line', id, cr)
        return r_id

res_partner()
