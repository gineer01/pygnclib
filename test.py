#!/usr/bin/env python
#
# This file is part of the pygnclib project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import sys, gzip
import pyxb
import pyxb.utils.domutils

import gnucash, cd, ts   # Bindings generated by PyXB
import _nsgroup as ns

# meh, for export, have to manually declare namespace prefixes
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_act, 'act')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_addr, 'addr')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_bgt, 'bgt')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_billterm, 'billterm')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_book, 'book')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_bt_days, 'bt-days')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_bt_prox, 'bt-prox')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(cd.Namespace, 'cd')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_cmdty, 'cmdty')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_cust, 'cust')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_employee, 'employee')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_gnc, 'gnc')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_invoice, 'invoice')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_job, 'job')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_lot, 'lot')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_order, 'order')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_owner, 'owner')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_price, 'price')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_recurrence, 'recurrence')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_slot, 'slot')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_split, 'split')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_sx, 'sx')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_taxtable, 'taxtable')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_trn, 'trn')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ts.Namespace, 'ts')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_tte, 'tte')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(ns._Namespace_vendor, 'vendor')

# main script
if len(sys.argv) > 1:
    gcfile = sys.argv[1]
else:
    print "Usage: gnuc2csv.py <gnucash_file> <account_guid>"
    exit(1)

# read GnuCash Data
try:
    f = gzip.open(gcfile)
    gcxml = f.read()
except:
    f = open(gcfile)
    gcxml = f.read()

try:
    doc = gnucash.CreateFromDocument(
          gcxml,
          location_base=gcfile)
    #pyxb.RequireValidWhenGenerating(False)
    dom = doc.toDOM()
    print dom.toprettyxml(indent=" ", encoding='utf-8')
except pyxb.UnrecognizedContentError as e:
    print '*** ERROR validating input:'
    print 'Unrecognized element "%s" at %s (details: %s)' % (e.content.expanded_name, e.content.location, e.details())
except pyxb.UnrecognizedDOMRootNodeError as e:
    print '*** ERROR matching content:'
    print e.details()
