##############################################################################
#
# Copyright (c) 2011 Latinux Inc (http://www.corvus.com.ve/) All Rights Reserved.
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

from osv import fields, osv
import time
import mx.DateTime
from mx.DateTime import RelativeDateTime



class sale_commissionsyear(osv.osv):
    _name = "sale.commissionsyear"
    _description = "Sale Commissions Year"
    _columns = {
        'name': fields.char('Commissions Year', size=64, required=True, states={'done':[('readonly',True)]}),
        'code': fields.char('Code', size=6, required=True, states={'done':[('readonly',True)]}),
        'company_id': fields.many2one('res.company', 'Company', states={'done':[('readonly',True)]}),
        'date_start': fields.date('Start Date', required=True, states={'done':[('readonly',True)]}),
        'date_stop': fields.date('End Date', required=True, states={'done':[('readonly',True)]}),
        'period_ids': fields.one2many('sale.commissionsperiod', 'commissionsyear_id', 'Periods', states={'done':[('readonly',True)]}),  
        'state': fields.selection([('draft','Draft'), ('done','Done')], 'Status', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'draft',
    }
    _order = "date_start"

    def _check_duration(self,cr,uid,ids):
        pgy_obj=self.browse(cr,uid,ids[0])
        if pgy_obj.date_stop < pgy_obj.date_start:
            return False
        return True

    _constraints = [
        (_check_duration, 'Error ! Periodo anual de comissiones invalido. ', ['date_stop'])
    ]

    def create_commissions_periods(self,cr, uid, ids, context={}, interval=1):
        for gy in self.browse(cr, uid, ids, context):
            ds = mx.DateTime.strptime(gy.date_start, '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d')<gy.date_stop:
                de = ds + RelativeDateTime(months=interval, days=-1)

                if de.strftime('%Y-%m-%d')>gy.date_stop:
                    de=mx.DateTime.strptime(gy.date_stop, '%Y-%m-%d')

                self.pool.get('sale.commissionsperiod').create(cr, uid, {
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'commissionsyear_id': gy.id,
                })
                ds = ds + RelativeDateTime(months=interval)
        return True

    def find(self, cr, uid, dt=None, exception=True, context={}):
        if not dt:
            dt = time.strftime('%Y-%m-%d')
        ids = self.search(cr, uid, [('date_start', '<=', dt), ('date_stop', '>=', dt)])
        if not ids:
            if exception:
                raise osv.except_osv(_('Error !'), _('No existe un periodo de comisiones definido !\nPor Favor cree uno.'))
            else:
                return False
        return ids[0]

    def action_year2draft(self, cr, uid, ids, *args):
        if not ids:
            return True
        year_id = ids[0]
        cr.execute('update sale_commissionsyear set state=%s where id=%s', ('draft', year_id))
        return True

sale_commissionsyear()


class sale_commissionsperiod(osv.osv):
    _name = "sale.commissionsperiod"
    _description = "Sale Commissions period"
    _columns = {
        'name': fields.char('Period Name', size=64, required=True, states={'done':[('readonly',True)]}),
        'code': fields.char('Code', size=12, states={'done':[('readonly',True)]}),
        'percent': fields.float('Percentage', digits=(16,2)),
        'date_start': fields.date('Start of Period', required=True, states={'done':[('readonly',True)]}),
        'date_stop': fields.date('End of Period', required=True, states={'done':[('readonly',True)]}),
        'commissionsyear_id': fields.many2one('sale.commissionsyear', 'Commissions Year', required=True, states={'done':[('readonly',True)]}, select=True),
        'state': fields.selection([('draft','Draft'), ('done','Done')], 'Status', readonly=True)
    }
    _defaults = {
        'state': lambda *a: 'draft',
    }
    _order = "date_start"

    def _check_duration(self,cr,uid,ids,context={}):
        obj_period=self.browse(cr,uid,ids[0])
        if obj_period.date_stop < obj_period.date_start:
            return False
        return True

    def _check_year_limit(self,cr,uid,ids,context={}):
        for obj_period in self.browse(cr,uid,ids):
            if obj_period.commissionsyear_id.date_stop < obj_period.date_stop or \
               obj_period.commissionsyear_id.date_stop < obj_period.date_start or \
               obj_period.commissionsyear_id.date_start > obj_period.date_start or \
               obj_period.commissionsyear_id.date_start > obj_period.date_stop:
                return False

            pids = self.search(cr, uid, [('date_stop','>=',obj_period.date_start),('date_start','<=',obj_period.date_stop),('id','<>',obj_period.id)])
            for period in self.browse(cr, uid, pids):
                if period.commissionsyear_id.company_id.id==obj_period.commissionsyear_id.company_id.id:
                    return False
        return True

    _constraints = [
        (_check_duration, 'Error ! Fecha del periodo de comision invalida ', ['date_stop']),
        (_check_year_limit, 'Periodo Invalido ! Las Fechas no se pueden solapar. ', ['date_stop'])
    ]

    def next(self, cr, uid, period, step, context={}):
        ids = self.search(cr, uid, [('date_start','>',period.date_start)])
        if len(ids)>=step:
            return ids[step-1]
        return False

    def find(self, cr, uid, dt=None, tp='all', context={}):
        if not dt:
            dt = time.strftime('%Y-%m-%d')
        crit = [('date_start','<=',dt),('date_stop','>=',dt),('state','=','draft')]
        ids = self.search(cr, uid, crit)
        if not ids:
            crit = [('date_start','<=',dt),('date_stop','>=',dt),('state','=','draft')]
            ids = self.search(cr, uid, crit)
            if not ids:
                raise osv.except_osv(_('Error !'), _('No hay fecha definida para el periodo..!\nPor Favor cree una.'))
        return ids

    def action_period2draft(self, cr, uid, ids, *args):
        if not ids:
            return True
        period_id = ids[0]
        period_obj=self.browse(cr,uid,ids[0])
        if period_obj.commissionsyear_id.state == 'done':
            raise osv.except_osv(_('Error !'), _('No es posible reabrir un periodo. El periodo anual esta cerrado...'))
        cr.execute('update sale_commissionsperiod set state=%s where id=%s', ('draft', period_id))
        return True

    def unlink(self, cr, uid, ids, context=None):
        if ids:
            period_id = ids[0]
            sql = 'select id from commissions_seller where commission_period_id=%d'%period_id
            cr.execute(sql)
            res = cr.dictfetchone()
            if res:
                raise osv.except_osv(_('Error !'), _('No puede borrar un periodo que posea comisiones ya calculadas...!'))
        return super(sale_commissionsperiod, self).unlink(cr, uid, ids, context)

sale_commissionsperiod()


