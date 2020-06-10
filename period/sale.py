# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Latinux Inc (http://www.latinux.com/) All Rights Reserved.
#                    Javier Duran <jduran@corvus.com.ve>
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

from osv import osv, fields



class sale_order(osv.osv):
    _description = "sale with general period"
    _inherit='sale.order'

    def _check_date(self,cr,uid,ids):
        pgp_obj = self.pool.get('period.generalperiod')
        for sale in self.browse(cr,uid,ids):
            flag = False
            date = sale.date_order
            if date:
                crit = [('date_start','<=',date),('date_stop','>=',date),('state','=','draft'),('type','=','sale')]
                res = pgp_obj.search(cr, uid, crit)
                if res:
                    flag = True
                else:
                    crit = [('date_start','<=',date),('date_stop','>=',date),('state','=','draft'),('type','=','all')]
                    res = pgp_obj.search(cr, uid, crit)
                    if res:
                        flag = True

        return flag


    _constraints = [
        (_check_date, 'Sale Order Error ! Could not validate the date, The date is not in an open period, please change the date ', ['date'])
    ]

sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

