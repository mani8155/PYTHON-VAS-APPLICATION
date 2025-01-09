import json
import time
from datetime import datetime
from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import session, Session
import models
from database import get_db
from models import *
import asyncio
from num2words import num2words
import logging
import requests as req
import base64

app = FastAPI()

logging.basicConfig(
    filename='logs.log',
    encoding='utf-8',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p'
)


def capitalize_each_word(text):
    return ' '.join(word[0].upper() + word[1:] if word else '' for word in text.split())


def b2e_tbl_col_feeonlinepayment_tbl(id, db: Session):
    print("function working")
    obj = db.query(FeeOnlinePayment).filter(FeeOnlinePayment.fop_id == id).first()

    print(obj)

    if not obj:
        logging.error(f"No FeeOnlinePayment record found with id {id}")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E", "errorlog": f"No FeeOnlinePayment record found with id {id}"})
        db.commit()
        return

    pay_input_obj = db.query(models.FeeOnlinePaymentInput).filter(
        models.FeeOnlinePaymentInput.fopt_tranno == obj.fop_tranno
    ).first()

    # print(pay_input_obj)

    if pay_input_obj is None:
        # print(f"FeeOnlinePaymentInput table does not match {obj.fop_tranno}")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E", "errorlog": f"FeeOnlinePaymentInput table does not match {obj.fop_tranno}"})
        db.commit()
        return

    fopt_id = pay_input_obj.fopt_json
    cleaned_string = fopt_id.replace(" ", "")
    # print(fopt_id)

    # url = f"https://api.hcaschennai.edu.in/sqlviews/api/v1/get_respone_data"
    url = f"http://192.168.4.220:8009/sqlviews/api/v1/get_respone_data"

    payload = json.dumps({
        "psk_uid": "d36c8e3d-74f5-4bf6-b8c2-a1dfa980a3f3",
        "project": "public",
        "data": {
            "uuid": cleaned_string
        }
    })

    # print(payload)
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("POST", url, headers=headers, data=payload)
    # print(response.text)
    if response.status_code == 204:
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({
            "status": "E",
            "errorlog": "status_code: 204, message: No Content."
        })
        db.commit()
        return

    if response.text == "null":
        # print(f"'{cleaned_string}' in the Postgres 'api_hcas_onlinepayment' table in uuid does not match")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E",
                  "errorlog": f"'{cleaned_string}' in the Postgres 'api_hcas_onlinepayment' table in uuid does not match"})
        db.commit()
        return

    res_data = response.json()[0]

    if res_data:

        transaction_id = res_data['transaction_id']
        print("transaction_id", transaction_id)

        if transaction_id and transaction_id.isdigit():
            # print(transaction_id)

            loan_pay_tbl = db.query(LoanRepayMent).filter(LoanRepayMent.sloanpid == int(transaction_id)).first()
            if loan_pay_tbl:
                # print("tbl :", loan_pay_tbl.sloanppayamt)
                loan_pay_tbl.sloanppaidamount = loan_pay_tbl.sloanppayamt
                loan_pay_tbl.sloanppaidon = datetime.now()
                loan_pay_tbl.sloanppaidsts = 2

                db.commit()
            else:
                logging.error(f"No matching loan repayment found for transaction ID: {transaction_id}")

        encoded_string = res_data['json_payload']

        decoded_bytes = base64.b64decode(encoded_string)

        decoded_string = decoded_bytes.decode('utf-8')

        # print(decoded_string)

        decoded_json = json.loads(decoded_string)
        # print(decoded_json)

        student_payment_obj = decoded_json['feedetails']

        logging.info(f"Student Payment Json : {student_payment_obj}")

        total_amount = 0.0

        for tot_amt in student_payment_obj:
            total_amount += float(tot_amt['feeamt'])

        total_amount_value = int(total_amount)
        num_in_words = num2words(total_amount_value)
        num_in_words_capitalized = capitalize_each_word(num_in_words)
        total_amount_in_words = f"INR (Rupees) {num_in_words_capitalized} Only"

        doc_id_obj = db.query(models.FeeCounter).filter(models.FeeCounter.id == 24).first()
        seq_no = doc_id_obj.seqno
        seq_prefix = doc_id_obj.seqprefix
        doc_id = f"{seq_prefix}-{seq_no}"

        doc_date = obj.fop_date
        student_id = obj.fop_stdkey

        doctype = "receipt"
        status = 0
        currency_type = 1
        currency_value = 1

        billing_year = "BILLING YEAR"

        student_year_obj = db.query(models.StudentInfo).filter(models.StudentInfo.stu_KEY == student_id).first()
        student_year = student_year_obj.stu_year

        created_by = obj.createdby
        current_time = datetime.now()
        lastmodifyby = None
        lastmodifyon = None
        imprefid = None
        counterid = 24

        save_tbl1 = FeeRecPay(
            docid=doc_id,
            docdate=doc_date,
            studentid=student_id,
            doctype=doctype,
            status=status,
            currencytype=currency_type,
            currrencyvalue=currency_value,
            billingyear=billing_year,
            studentyear=student_year,
            totalamt=total_amount_value,
            amtinwords=total_amount_in_words,
            createdby=created_by,
            createdon=current_time,
            lastmodifyby=lastmodifyby,
            lastmodifyon=lastmodifyon,
            imprefid=imprefid,
            counterid=counterid
        )

        db.add(save_tbl1)
        db.commit()
        db.refresh(save_tbl1)

        logging.info(f"The record in the 'b2e_tbl_col_feerecpay' table was updated successfully.")

        tbl1_id = save_tbl1.feerpid

        pay_paments_tbl = FeeRecipePayPayments(
            feesrpid=tbl1_id,
            paymentmode="ONLINE",
            amount=total_amount_value,
            refno=doc_id,
            refdate=doc_date,
            bankname=None,
            status='0'
        )

        db.add(pay_paments_tbl)
        db.commit()
        db.refresh(pay_paments_tbl)

        logging.info(f"The record in the 'b2e_tbl_col_feerecpaypayments' table was updated successfully.")

        feetypeid = None

        for child_rec in student_payment_obj:
            save_tbl2 = FeeRecPayDetail(
                feesrpid=tbl1_id,
                feetypeid=feetypeid,
                feeid=child_rec['feeid'],
                feeamount=child_rec['feeamt'],
                remarks=None,
                status=0,
                imprefid=None,
                acdyear=24,
            )

            db.add(save_tbl2)
            db.commit()
            db.refresh(save_tbl2)

        doc_id_obj.seqno += 1

        logging.info(f"The record in the 'b2e_tbl_col_feerecpaydetail' table was updated successfully.")

        db.add(doc_id_obj)
        db.commit()
        db.refresh(doc_id_obj)

        for child_rec2 in student_payment_obj:
            crdamt = child_rec2['feeamt']

            cradmant = -1 * float(crdamt)

            ledger = FeeLedger(
                docno=doc_id,
                docdate=doc_date,
                doctype=doctype,
                totalamt=total_amount_value,
                curtype=1,
                curvalue=1,
                acdyear=24,
                studid=student_id,
                counterid=24,
                studyear=student_year,
                feeid=child_rec2['feeid'],
                amount=child_rec2['feeamt'],
                remarks=None,
                status=0,
                srcid=0,
                srcdtlid=0,
                plusminus="M",
                crdramt=cradmant,
                createdby=created_by,
                createdon=current_time,
                modifyby=None,
                modifyon=None
            )

            db.add(ledger)
            db.commit()
            db.refresh(ledger)

        logging.info(f"The record in the 'b2e_tbl_col_feeledger' table was updated successfully.")

        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "P"})
        db.commit()

        logging.info(f"The record '{id}' in the TransferLogTable Updated Status 'P' ")
        logging.info(f"The record with ID '{id}' has been successfully updated in 3 tables.")

        print("successfully updated")

    else:
        print(f"Error : {fopt_id}")
        print("Data not retrieved by SQL Views")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E", "errorlog": f"Data not retrieved by SQL Views {fopt_id}"})
        db.commit()
        return


def en_flow_func(id, db: Session):
    obj = db.query(FeeOnlinePayment).filter(FeeOnlinePayment.fop_id == id).first()
    print(obj)


    if not obj:
        logging.error(f"No FeeOnlinePayment record found with id {id}")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E", "errorlog": f"No FeeOnlinePayment record found with id {id}"})
        db.commit()
        return

    pay_input_obj = db.query(models.FeeOnlinePaymentInput).filter(
        models.FeeOnlinePaymentInput.fopt_tranno == obj.fop_tranno
    ).first()

    # print(pay_input_obj)

    if pay_input_obj is None:
        # print(f"FeeOnlinePaymentInput table does not match {obj.fop_tranno}")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E", "errorlog": f"FeeOnlinePaymentInput table does not match {obj.fop_tranno}"})
        db.commit()
        return

    fopt_id = pay_input_obj.fopt_json
    uuid = fopt_id.replace(" ", "")
    print(uuid, "uuid")


    # url = f"https://api.hcaschennai.edu.in/sqlviews/api/v1/get_respone_data"
    url = f"http://192.168.4.220:8009/sqlviews/api/v1/get_respone_data"

    payload = json.dumps({
        "psk_uid": "25550f47-3041-4f5f-9652-3607a6bb3e75",
        "project": "public",
        "data": {
            "uuid": uuid
        }
    })

    # print(payload)
    headers = {
        'Content-Type': 'application/json'
    }

    response = req.request("POST", url, headers=headers, data=payload)
    # print(response.text)

    if response.status_code == 204:
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({
            "status": "E",
            "errorlog": "status_code: 204, message: No Content."
        })
        db.commit()
        return

    if response.text == "null":
        # print(f"'{cleaned_string}' in the Postgres 'api_hcas_onlinepayment' table in uuid does not match")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E",
                  "errorlog": f"'{uuid}' in the Postgres 'api_hcas_onlinepayment' table in uuid does not match"})
        db.commit()
        return

    res_data = response.json()[0]

    if res_data:

        transaction_id = res_data['transaction_id']
        print("transaction_id", transaction_id)

        if transaction_id and transaction_id.isdigit():
            # print(transaction_id)

            loan_pay_tbl = db.query(LoanRepayMent).filter(LoanRepayMent.sloanpid == int(transaction_id)).first()
            if loan_pay_tbl:
                # print("tbl :", loan_pay_tbl.sloanppayamt)
                loan_pay_tbl.sloanppaidamount = loan_pay_tbl.sloanppayamt
                loan_pay_tbl.sloanppaidon = datetime.now()
                loan_pay_tbl.sloanppaidsts = 2

                db.commit()
            else:
                logging.error(f"No matching loan repayment found for transaction ID: {transaction_id}")

        encoded_string = res_data['json_payload']

        decoded_bytes = base64.b64decode(encoded_string)

        decoded_string = decoded_bytes.decode('utf-8')

        # print(decoded_string)

        decoded_json = json.loads(decoded_string)
        # print(decoded_json)

        student_payment_obj = decoded_json['feedetails']

        logging.info(f"Student Payment Json : {student_payment_obj}")

        total_amount = 0.0

        for tot_amt in student_payment_obj:
            total_amount += float(tot_amt['feeamt'])

        total_amount_value = int(total_amount)
        num_in_words = num2words(total_amount_value)
        num_in_words_capitalized = capitalize_each_word(num_in_words)
        total_amount_in_words = f"INR (Rupees) {num_in_words_capitalized} Only"

        doc_id_obj = db.query(models.FeeCounter).filter(models.FeeCounter.id == 24).first()
        seq_no = doc_id_obj.seqno
        seq_prefix = doc_id_obj.seqprefix
        doc_id = f"{seq_prefix}-{seq_no}"

        doc_date = obj.fop_date
        student_id = obj.fop_stdkey

        doctype = "receipt"
        status = 0
        currency_type = 1
        currency_value = 1

        billing_year = "BILLING YEAR"

        student_year_obj = db.query(models.StudentInfo).filter(models.StudentInfo.stu_KEY == student_id).first()
        student_year = student_year_obj.stu_year

        created_by = obj.createdby
        current_time = datetime.now()
        lastmodifyby = None
        lastmodifyon = None
        imprefid = None
        counterid = 24

        save_tbl1 = FeeRecPay(
            docid=doc_id,
            docdate=doc_date,
            studentid=student_id,
            doctype=doctype,
            status=status,
            currencytype=currency_type,
            currrencyvalue=currency_value,
            billingyear=billing_year,
            studentyear=student_year,
            totalamt=total_amount_value,
            amtinwords=total_amount_in_words,
            createdby=created_by,
            createdon=current_time,
            lastmodifyby=lastmodifyby,
            lastmodifyon=lastmodifyon,
            imprefid=imprefid,
            counterid=counterid
        )

        db.add(save_tbl1)
        db.commit()
        db.refresh(save_tbl1)

        logging.info(f"The record in the 'b2e_tbl_col_feerecpay' table was updated successfully.")

        tbl1_id = save_tbl1.feerpid

        pay_paments_tbl = FeeRecipePayPayments(
            feesrpid=tbl1_id,
            paymentmode="ONLINE",
            amount=total_amount_value,
            refno=doc_id,
            refdate=doc_date,
            bankname=None,
            status='0'
        )

        db.add(pay_paments_tbl)
        db.commit()
        db.refresh(pay_paments_tbl)

        logging.info(f"The record in the 'b2e_tbl_col_feerecpaypayments' table was updated successfully.")

        feetypeid = None

        for child_rec in student_payment_obj:
            save_tbl2 = FeeRecPayDetail(
                feesrpid=tbl1_id,
                feetypeid=feetypeid,
                feeid=child_rec['feeid'],
                feeamount=child_rec['feeamt'],
                remarks=None,
                status=0,
                imprefid=None,
                acdyear=24,
            )

            db.add(save_tbl2)
            db.commit()
            db.refresh(save_tbl2)

        doc_id_obj.seqno += 1

        logging.info(f"The record in the 'b2e_tbl_col_feerecpaydetail' table was updated successfully.")

        db.add(doc_id_obj)
        db.commit()
        db.refresh(doc_id_obj)

        for child_rec2 in student_payment_obj:
            crdamt = child_rec2['feeamt']

            cradmant = -1 * float(crdamt)

            ledger = FeeLedger(
                docno=doc_id,
                docdate=doc_date,
                doctype=doctype,
                totalamt=total_amount_value,
                curtype=1,
                curvalue=1,
                acdyear=24,
                studid=student_id,
                counterid=24,
                studyear=student_year,
                feeid=child_rec2['feeid'],
                amount=child_rec2['feeamt'],
                remarks=None,
                status=0,
                srcid=0,
                srcdtlid=0,
                plusminus="M",
                crdramt=cradmant,
                createdby=created_by,
                createdon=current_time,
                modifyby=None,
                modifyon=None
            )

            db.add(ledger)
            db.commit()
            db.refresh(ledger)

        logging.info(f"The record in the 'b2e_tbl_col_feeledger' table was updated successfully.")

        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "P"})
        db.commit()

        logging.info(f"The record '{id}' in the TransferLogTable Updated Status 'P' ")
        logging.info(f"The record with ID '{id}' has been successfully updated in 3 tables.")

        print("successfully updated")

    else:
        print(f"Error : {uuid}")
        print("Data not retrieved by SQL Views")
        transfer_log = db.query(models.TransferLogTable).filter(
            models.TransferLogTable.record_id == id
        ).update({"status": "E", "errorlog": f"Data not retrieved by SQL Views {uuid}"})
        db.commit()
        return


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_status())


# async def check_status():
#     while True:
#         with next(get_db()) as db:
#             try:
#                 tra_log_obj = db.execute(
#                     select(TransferLogTable).filter(TransferLogTable.status == "N")).scalars().all()
#                 for obj in tra_log_obj:
#                     logging.info(f"TransferLogTable for records with status 'N' and record_id: {obj.record_id}.")
#                     b2e_tbl_col_feeonlinepayment_tbl(obj.record_id, db)
#             finally:
#                 db.close()
#
#         await asyncio.sleep(5)


async def check_status():
    while True:
        with next(get_db()) as db:
            try:
                # tra_log_obj = db.execute(
                #     select(TransferLogTable).filter(
                #         and_(
                #             TransferLogTable.status == "N" or "EN",
                #             TransferLogTable.source_api == "Receipt"
                #         )
                #     )
                # ).scalars().all()

                tra_log_obj = db.execute(
                    select(TransferLogTable).where(
                        and_(
                            or_(
                                TransferLogTable.status == "N",
                                TransferLogTable.status == "EN"
                            ),
                            TransferLogTable.source_api == "Receipt"
                        )
                    )
                ).scalars().all()

                for obj in tra_log_obj:
                    logging.info(f"TransferLogTable for records with status 'N' and record_id: {obj.record_id}.")
                    print(obj.source_sql)
                    if obj.status == "EN":
                        print("condition work")
                        en_flow_func(obj.record_id, db)
                    else:
                        b2e_tbl_col_feeonlinepayment_tbl(obj.record_id, db)
            except Exception as e:
                print(f"An error occurred: {e}")
        await asyncio.sleep(5)
