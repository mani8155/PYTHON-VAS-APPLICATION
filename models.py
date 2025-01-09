from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class TransferLogTable(Base):
    __tablename__ = 'transferlog'

    uuid = Column(Integer, primary_key=True, index=True)
    source_api = Column(String(255))
    source_tablename = Column(String(255))
    record_id = Column(String(255))
    errorlog = Column(String(255))
    source_sql = Column(String(255))
    status = Column(String(3))


class StudentInfo(Base):
    __tablename__ = 'b2e_tbl_id_stu_personal_info'

    stu_KEY = Column(Integer, primary_key=True, index=True)
    stu_year = Column(String(255))


class FeeOnlinePayment(Base):
    __tablename__ = 'b2e_tbl_col_feeonlinepayment'

    fop_id = Column(Integer, primary_key=True, index=True)
    fop_tranno = Column(String(255))
    fop_date = Column(DateTime)
    fop_banktokenid = Column(String(255))
    fop_bankrefno = Column(String(255))
    fop_totalamt = Column(String(255))
    fop_stdkey = Column(String(255))
    fop_stdrefno = Column(String(255))
    fop_status = Column(String(255))
    createdby = Column(String(255))
    createdon = Column(DateTime)


class FeeOnlinePaymentInput(Base):
    __tablename__ = 'b2e_tbl_col_feeonlinepaymentinput'

    fopt_id = Column(Integer, primary_key=True, index=True)
    fopt_tranno = Column(String(255))
    fopt_json = Column(String(255))
    tcreatedby = Column(String(255))
    tcreatedon = Column(String(255))


class FeeCounter(Base):
    __tablename__ = 'b2e_tbl_col_feecounter'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    seqtype = Column(String(255))
    seqprefix = Column(String(255))
    seqno = Column(String(255))
    status = Column(String(255))
    seqauto = Column(String(255))


class FeeRecPay(Base):
    __tablename__ = 'b2e_tbl_col_feerecpay'

    feerpid = Column(Integer, primary_key=True, index=True)
    docid = Column(String(255))
    docdate = Column(DateTime)
    studentid = Column(String(255))
    doctype = Column(String(255))
    status = Column(String(255))
    currencytype = Column(String(255))
    currrencyvalue = Column(String(255))
    billingyear = Column(String(255))
    studentyear = Column(String(255))
    totalamt = Column(String(255))
    amtinwords = Column(String(255))
    createdby = Column(String(255))
    createdon = Column(DateTime)
    lastmodifyby = Column(String(255))
    lastmodifyon = Column(String(255))
    imprefid = Column(String(255))
    counterid = Column(String(255))


class FeeRecPayDetail(Base):
    __tablename__ = 'b2e_tbl_col_feerecpaydetail'

    feesrpdetailid = Column(Integer, primary_key=True, index=True)
    feesrpid = Column(Integer)
    feetypeid = Column(Integer)
    feeid = Column(Integer)
    feeamount = Column(Integer)
    remarks = Column(String(255))
    status = Column(String(255))
    imprefid = Column(String(255))
    acdyear = Column(Integer)


class FeeLedger(Base):
    __tablename__ = 'b2e_tbl_col_feeledger'

    feeledgerid = Column(Integer, primary_key=True, index=True)
    docno = Column(String(255))
    docdate = Column(DateTime)
    doctype = Column(String(255))
    totalamt = Column(Integer)
    curtype = Column(Integer)
    curvalue = Column(Integer)
    acdyear = Column(Integer)
    counterid = Column(Integer)
    studid = Column(Integer)
    studyear = Column(String(255))
    feeid = Column(Integer)
    amount = Column(Integer)
    remarks = Column(String(255))
    srcid = Column(Integer)
    srcdtlid = Column(Integer)
    plusminus = Column(String(255))
    crdramt = Column(Integer)
    status = Column(String(255))
    createdby = Column(String(255))
    createdon = Column(DateTime)
    modifyby = Column(String(255))
    modifyon = Column(String(255))


class FeeRecipePayPayments(Base):
    __tablename__ = 'b2e_tbl_col_feerecpaypayments'

    idrcp = Column(Integer, primary_key=True, index=True)
    feesrpid = Column(Integer)
    paymentmode = Column(String(255))
    amount = Column(Integer)
    refno = Column(String(255))
    refdate = Column(DateTime)
    bankname = Column(String(255))
    status = Column(String(255))


class LoanRepayMent(Base):
    __tablename__ = 'b2e_tbl_col_stu_loanrepayment'

    sloanpid = Column(Integer, primary_key=True, index=True)
    sloanppayamt = Column(Integer)
    sloanppaidon = Column(DateTime)
    sloanppaidsts = Column(Integer)
    sloanppaidamount = Column(Integer)

