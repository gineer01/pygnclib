#!/usr/bin/env python
#
# This file is part of the pygnclib project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

import sys, gzip, uuid
import pyxb, csv, argparse

import gnucash, gnc, trn, cmdty, ts, split   # Bindings generated by PyXB
from datetime import date, datetime
from fractions import Fraction

# meh, for export, have to manually declare namespace prefixes
import cd
import _nsgroup as ns
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

# assemble transaction date from PayPal CSV line
def dateFromPayPalLine(line):
    payment_date = datetime.strptime(
        line["Date"] + " " + line[" Time"],
        '%d.%m.%Y %H:%M:%S')
# %z seems fixed only in 3.2
#            line["Date"] + " " + line[" Time"] + " " + line[" Time Zone"],
#            '%d.%m.%Y %H:%M:%S GMT%z').utcoffsetset()
    return payment_date.strftime('%Y-%m-%d %H:%M:%S +0100')

# convert float from paypal number string
def amountFromPayPal(value):
    # assume German locale here for the while
    minusIdx = value.find("-")
    preMult  = 1
    if minusIdx != -1:
        value = value[minusIdx+1:]
        preMult  = -1
    # kill all thousands separators, split off fractional part
    value_parts = value.replace(".","").split(',')
    if len(value_parts) == 1:
        return preMult * float(value_parts[0])
    if len(value_parts) == 2:
        return preMult * (float(value_parts[0]) + float(value_parts[1])/(10**len(value_parts[1])))
    else:
        raise IndexError

# convert number to integer string (possibly via conversion to rational number)
def gnucashFromAmount(value):
    rational_value = Fraction(value).limit_denominator(1000)
    return str(rational_value.numerator)+"/"+str(rational_value.denominator)

# lookup account with given name in dict (or search in xml tree)
def lookupAccountUUID(accounts, xml_tree, account_name):
    if accounts.has_key(account_name):
        return accounts[account_name]
    else:
        for elem in xml_tree:
            # get account with matching name (partial match is ok)
            if elem.name.find(account_name) != -1:
                accounts[account_name] = elem.id.value()
                return elem.id.value()
    print "Did not find account with name %s in current book, bailing out!" % account_name
    exit(1)

# enter current time as "date entered"
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S +0100')

# add a gnucash split transaction with the given data
def createTransaction(transaction_date, account1_uuid, account1_memo, account2_uuid, account2_memo,
                      transaction_currency, transaction_value, transaction_description):
    try:
        transaction_amount = amountFromPayPal(transaction_value)

        # create a new transaction with two splits - just lovely this
        # pyxb design - the below is written by _just_ looking at the
        # rng schema
        return gnc.transaction(
            trn.id( uuid.uuid4().hex, type="guid" ),
            trn.currency( cmdty.space("ISO4217"), cmdty.id(transaction_currency) ),
            trn.date_posted( ts.date(transaction_date) ),
            trn.date_entered( ts.date(now) ),
            trn.description(transaction_description),
            trn.splits(
                trn.split(
                    split.id( uuid.uuid4().hex, type="guid" ),
                    split.memo( account1_memo ),
                    split.reconciled_state( "n" ),
                    split.value( gnucashFromAmount(transaction_amount) ),
                    split.quantity( gnucashFromAmount(transaction_amount) ),
                    split.account( account1_uuid, type="guid" )),
                trn.split(
                    split.id( uuid.uuid4().hex, type="guid" ),
                    split.memo( account2_memo ),
                    split.reconciled_state( "n" ),
                    split.value( gnucashFromAmount(-transaction_amount) ),
                    split.quantity( gnucashFromAmount(-transaction_amount) ),
                    split.account( account2_uuid, type="guid" ))),
            version="2.0.0" )
    except pyxb.UnrecognizedContentError as e:
        print '*** ERROR validating input:'
        print 'Unrecognized element "%s" at %s (details: %s)' % (e.content.expanded_name, e.content.location, e.details())

def default_importer(addTransaction, account1_uuid, account2_uuid, transaction_type, name,
                     transaction_date, transaction_state, transaction_currency, transaction_real_currency, transaction_gross,
                     transaction_fee, transaction_net, transaction_value, transaction_id, transaction_comment):
    return addTransaction(transaction_date, account1_uuid, "Unknown transaction",
                          account2_uuid, "Unknown PayPal", transaction_currency, transaction_value,
                          "PayPal %s from %s - state: %s - ID: %s - gross: %s %s - fee: %s %s - net %s %s %s" % (transaction_type, name, transaction_state,
                                                                                                                 transaction_id, transaction_real_currency,
                                                                                                                 transaction_gross, transaction_real_currency,
                                                                                                                 transaction_fee, transaction_real_currency,
                                                                                                                 transaction_net, transaction_comment))

# main script
parser = argparse.ArgumentParser(description="Import PayPal transactions from CSV",
                                 epilog="Extend this script by plugin snippets, that are simple python scripts with the following "
                                 "at the toplevel namespace (example):"
                                 "type_and_state = 'DonationsCompleted'"
                                 "account1_name  = 'PayPal'"
                                 "account2_name  = 'Donations'"
                                 "def importer(funcCreateTrns, 14args): return funcCreateTrns(...)")
parser.add_argument("-v", "--verbosity", action="count", default=0, help="Increase verbosity by one")
parser.add_argument("-p", "--pretty", action="store_true", default=False, help="Export xml pretty-printed")
parser.add_argument("-d", "--delimiter", default='\t', help="Delimiter used in the CSV file")
parser.add_argument("-q", "--quotechar", default='"', help="Quote character used in the CSV file")
parser.add_argument("-e", "--encoding", default='iso-8859-1', help="Character encoding used in the CSV file")
parser.add_argument("-s", "--script", action="append", help="Plugin snippets for sorting into different accounts")
parser.add_argument("ledger_gnucash", help="GnuCash ledger you want to import into")
parser.add_argument("paypal_csv", help="PayPal CSV export you want to import")
parser.add_argument("output_gnucash", help="Output GnuCash ledger file")
args = parser.parse_args()

gncfile = args.ledger_gnucash
csvfile = args.paypal_csv
outfile = args.output_gnucash

# read GnuCash data
try:
    f = gzip.open(gncfile)
    gncxml = f.read()
except:
    f = open(gncfile)
    gncxml = f.read()

# read paypal csv data
paypal_csv = csv.DictReader(open(csvfile), delimiter=args.delimiter, quotechar=args.quotechar)

try:
    doc = gnucash.CreateFromDocument(
        gncxml,
        location_base=gncfile)
except pyxb.UnrecognizedContentError as e:
    print '*** ERROR validating input:'
    print 'Unrecognized element "%s" at %s (details: %s)' % (e.content.expanded_name, e.content.location, e.details())
except pyxb.UnrecognizedDOMRootNodeError as e:
    print '*** ERROR matching content:'
    print e.details()

conversion_scripts = {}
# import conversion scripts
if args.script:
    for index,script in enumerate(args.script):
        ns_name = "script"+index
        exec "import "+script+" as "+ns_name
        conversion_scripts[eval(ns_name+".type_and_state")] = ns_name

accounts = {}
old_lines = []
for index,line in enumerate(paypal_csv):
    transaction_type = line[" Type"]

    # special-handling for currency conversion - we want all
    # transactions in EUR, thus we merge all three paypal transaction
    # (conversion from <currency>, conversion to EUR, original
    # transaction) into one
    if transaction_type == "Currency Conversion":
        old_lines.append( line )
    else:
        name = line[" Name"].decode(args.encoding)
        transaction_date = dateFromPayPalLine(line)
        transaction_state = line[" Status"]
        transaction_currency = line[" Currency"]
        transaction_real_currency = transaction_currency
        transaction_gross = line[" Gross"]
        transaction_fee = line[" Fee"]
        transaction_net = line[" Net"]
        transaction_id  = line[" Transaction ID"]
        transaction_value = transaction_net

        # to be extended for e.g. currency conversions
        transaction_comment = ""

        # merge previous currency conversions, if any
        if old_lines:
            if len(old_lines) != 2 or old_lines[0][" Currency"] != "EUR" or old_lines[0][" Status"] != "Completed":
                print "Inconsistent currency conversion in line %d, bailing out" % index
                exit(1)
            from_subject  = old_lines[0][" Name"]
            from_transID  = old_lines[0][" Transaction ID"]
            to_transID    = old_lines[1][" Transaction ID"]
            # clobber currency and value, the real ones are from old_lines[0]
            transaction_currency = old_lines[0][" Currency"]
            transaction_value = old_lines[0][" Net"]
            # and clear old lines for next triplet
            old_lines = []
            # and assemble comment string from the above
            transaction_comment = "[%s via %s and %s]" % (from_subject, from_transID, to_transID)

        if transaction_currency != "EUR":
            print "Wrong currency for main transaction encountered in line %d, bailing out" % index
            exit(1)

        # stick unmatched transactions into Imbalance account
        account1_name = "PayPal"
        account2_name = "Imbalance"
        importer = default_importer

        # find matching conversion script
        if conversion_scripts.has_key(transaction_type+transaction_state):
            account1_name = eval(conversion_scripts[transaction_type+transaction_state]+".account1_name")
            account2_name = eval(conversion_scripts[transaction_type+transaction_state]+".account2_name")
            importer = eval(conversion_scripts[transaction_type+transaction_state]+".importer")

        # obtain account UUIDs
        account1_uuid = lookupAccountUUID(accounts, doc.book.account, account1_name)
        account2_uuid = lookupAccountUUID(accounts, doc.book.account, account2_name)

        # run it
        new_trn = importer(createTransaction, account1_uuid, account2_uuid, transaction_type, name, transaction_date,
                           transaction_state, transaction_currency, transaction_real_currency, transaction_gross, transaction_fee,
                           transaction_net, transaction_value, transaction_id, transaction_comment)

        # add it to ledger
        doc.book.append(new_trn)

# write out amended ledger
out = open(outfile, "wb")
if args.pretty:
    dom = doc.toDOM()
    out.write( dom.toprettyxml(indent=" ", encoding='utf-8') )
else:
    out.write( doc.toxml(encoding='utf-8') )
