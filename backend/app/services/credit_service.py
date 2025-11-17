"""
Credit Service
سرویس مدیریت کریدیت نمایندگان
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import logging

from ..models import (
    CreditBalance, CreditTransaction, CreditPricing,
    User, Reseller, TransactionType, OperationType,
    ProductGroup, ServicePlan, ResellerGroup, CustomerAccount
)

logger = logging.getLogger(__name__)


class CreditService:
    """سرویس مدیریت کریدیت"""

    @staticmethod
    def get_or_create_balance(db: Session, user_id: str) -> CreditBalance:
        """
        دریافت موجودی کریدیت یا ایجاد در صورت عدم وجود

        Args:
            db: Database session
            user_id: شناسه کاربر

        Returns:
            CreditBalance: موجودی کریدیت
        """
        balance = db.query(CreditBalance).filter(
            CreditBalance.user_id == user_id
        ).first()

        if not balance:
            balance = CreditBalance(user_id=user_id, balance=Decimal(0))
            db.add(balance)
            db.commit()
            db.refresh(balance)
            logger.info(f"Created credit balance for user {user_id}")

        return balance

    @staticmethod
    def add_credit(
        db: Session,
        reseller_id: str,
        amount: Decimal,
        admin_id: Optional[str] = None,
        note: Optional[str] = None
    ) -> CreditTransaction:
        """
        افزودن کریدیت (شارژ دستی توسط ادمین)

        Args:
            db: Database session
            reseller_id: شناسه نماینده
            amount: مقدار کریدیت
            admin_id: شناسه ادمین
            note: یادداشت

        Returns:
            CreditTransaction: تراکنش ایجاد شده
        """
        if amount <= 0:
            raise ValueError("مقدار کریدیت باید مثبت باشد")

        balance = CreditService.get_or_create_balance(db, reseller_id)

        # ایجاد تراکنش
        transaction = CreditTransaction(
            reseller_id=reseller_id,
            type=TransactionType.MANUAL_ADD,
            operation=OperationType.MANUAL,
            amount=amount,
            balance_before=balance.balance,
            balance_after=balance.balance + amount,
            description=f"شارژ دستی: {amount} کریدیت",
            admin_note=note,
            created_by=admin_id
        )

        # بروزرسانی موجودی
        balance.balance += amount
        balance.updated_at = datetime.utcnow()

        # بروزرسانی آمار نماینده
        reseller = db.query(Reseller).filter(Reseller.user_id == reseller_id).first()
        if reseller:
            reseller.total_credit_purchased += amount

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Added {amount} credit to reseller {reseller_id}")
        return transaction

    @staticmethod
    def deduct_credit(
        db: Session,
        reseller_id: str,
        amount: Decimal,
        admin_id: Optional[str] = None,
        note: Optional[str] = None
    ) -> CreditTransaction:
        """
        کسر کریدیت (کسر دستی توسط ادمین)

        Args:
            db: Database session
            reseller_id: شناسه نماینده
            amount: مقدار کریدیت
            admin_id: شناسه ادمین
            note: یادداشت

        Returns:
            CreditTransaction: تراکنش ایجاد شده

        Raises:
            ValueError: اگر موجودی کافی نباشد
        """
        if amount <= 0:
            raise ValueError("مقدار کریدیت باید مثبت باشد")

        balance = CreditService.get_or_create_balance(db, reseller_id)

        if balance.balance < amount:
            raise ValueError(f"موجودی کافی نیست. موجودی فعلی: {balance.balance}")

        # ایجاد تراکنش
        transaction = CreditTransaction(
            reseller_id=reseller_id,
            type=TransactionType.MANUAL_DEDUCT,
            operation=OperationType.MANUAL,
            amount=-amount,
            balance_before=balance.balance,
            balance_after=balance.balance - amount,
            description=f"کسر دستی: {amount} کریدیت",
            admin_note=note,
            created_by=admin_id
        )

        # بروزرسانی موجودی
        balance.balance -= amount
        balance.updated_at = datetime.utcnow()

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Deducted {amount} credit from reseller {reseller_id}")
        return transaction

    @staticmethod
    def charge_for_operation(
        db: Session,
        reseller_id: str,
        operation_type: OperationType,
        product_group_id: str,
        service_plan_id: Optional[str] = None,
        account_id: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> tuple[CreditTransaction, Decimal]:
        """
        کسر کریدیت برای یک عملیات

        Args:
            db: Database session
            reseller_id: شناسه نماینده
            operation_type: نوع عملیات
            product_group_id: شناسه گروه محصول
            service_plan_id: شناسه پلن سرویس (اختیاری)
            account_id: شناسه اکانت (برای لینک)
            product_id: شناسه محصول (برای لینک)

        Returns:
            tuple: (تراکنش, مقدار کریدیت کسر شده)

        Raises:
            ValueError: اگر موجودی کافی نباشد یا قیمت یافت نشود
        """
        # دریافت قیمت
        cost = CreditService.get_operation_cost(
            db, reseller_id, operation_type, product_group_id, service_plan_id
        )

        if cost <= 0:
            logger.warning(f"Cost is 0 or negative for operation {operation_type}")
            return None, Decimal(0)

        # بررسی موجودی
        balance = CreditService.get_or_create_balance(db, reseller_id)
        if balance.balance < cost:
            raise ValueError(
                f"موجودی کریدیت کافی نیست. نیاز: {cost}، موجودی: {balance.balance}"
            )

        # ایجاد تراکنش
        transaction = CreditTransaction(
            reseller_id=reseller_id,
            type=TransactionType.PURCHASE,
            operation=operation_type,
            amount=-cost,
            balance_before=balance.balance,
            balance_after=balance.balance - cost,
            related_account_id=account_id,
            related_product_id=product_id,
            description=f"کسر کریدیت برای {operation_type.value}"
        )

        # بروزرسانی موجودی
        balance.balance -= cost
        balance.updated_at = datetime.utcnow()

        # بروزرسانی آمار نماینده
        reseller = db.query(Reseller).filter(Reseller.user_id == reseller_id).first()
        if reseller:
            reseller.total_credit_spent += cost

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Charged {cost} credit from reseller {reseller_id} for {operation_type}")
        return transaction, cost

    @staticmethod
    def refund_credit(
        db: Session,
        reseller_id: str,
        amount: Decimal,
        account_id: Optional[str] = None,
        product_id: Optional[str] = None,
        reason: str = "برگشت کریدیت"
    ) -> CreditTransaction:
        """
        برگشت کریدیت (مثلاً هنگام حذف اکانت)

        Args:
            db: Database session
            reseller_id: شناسه نماینده
            amount: مقدار کریدیت
            account_id: شناسه اکانت
            product_id: شناسه محصول
            reason: دلیل برگشت

        Returns:
            CreditTransaction: تراکنش
        """
        if amount <= 0:
            logger.warning(f"Refund amount is 0 or negative: {amount}")
            return None

        balance = CreditService.get_or_create_balance(db, reseller_id)

        # ایجاد تراکنش
        transaction = CreditTransaction(
            reseller_id=reseller_id,
            type=TransactionType.REFUND,
            operation=OperationType.DELETE,
            amount=amount,
            balance_before=balance.balance,
            balance_after=balance.balance + amount,
            related_account_id=account_id,
            related_product_id=product_id,
            description=reason
        )

        # بروزرسانی موجودی
        balance.balance += amount
        balance.updated_at = datetime.utcnow()

        # بروزرسانی آمار
        reseller = db.query(Reseller).filter(Reseller.user_id == reseller_id).first()
        if reseller:
            reseller.total_credit_spent = max(0, reseller.total_credit_spent - amount)

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Refunded {amount} credit to reseller {reseller_id}")
        return transaction

    @staticmethod
    def get_operation_cost(
        db: Session,
        reseller_id: str,
        operation_type: OperationType,
        product_group_id: str,
        service_plan_id: Optional[str] = None
    ) -> Decimal:
        """
        دریافت هزینه یک عملیات

        Args:
            db: Database session
            reseller_id: شناسه نماینده
            operation_type: نوع عملیات
            product_group_id: شناسه گروه محصول
            service_plan_id: شناسه پلن (اختیاری)

        Returns:
            Decimal: هزینه به کریدیت
        """
        # دریافت گروه نماینده
        reseller = db.query(Reseller).filter(Reseller.user_id == reseller_id).first()
        reseller_group_id = reseller.group_id if reseller else None

        # جستجوی قیمت با اولویت:
        # 1. قیمت اختصاصی برای گروه نماینده + پلن مشخص
        # 2. قیمت اختصاصی برای گروه نماینده (بدون پلن)
        # 3. قیمت عمومی + پلن مشخص
        # 4. قیمت عمومی (بدون پلن)
        # 5. قیمت پلن سرویس (پیش‌فرض)

        queries = [
            # با گروه نماینده + پلن
            and_(
                CreditPricing.product_group_id == product_group_id,
                CreditPricing.operation_type == operation_type,
                CreditPricing.service_plan_id == service_plan_id,
                CreditPricing.applies_to_reseller_group_id == reseller_group_id,
                CreditPricing.is_active == True
            ) if reseller_group_id and service_plan_id else None,
            # با گروه نماینده بدون پلن
            and_(
                CreditPricing.product_group_id == product_group_id,
                CreditPricing.operation_type == operation_type,
                CreditPricing.service_plan_id.is_(None),
                CreditPricing.applies_to_reseller_group_id == reseller_group_id,
                CreditPricing.is_active == True
            ) if reseller_group_id else None,
            # عمومی + پلن
            and_(
                CreditPricing.product_group_id == product_group_id,
                CreditPricing.operation_type == operation_type,
                CreditPricing.service_plan_id == service_plan_id,
                CreditPricing.applies_to_reseller_group_id.is_(None),
                CreditPricing.is_active == True
            ) if service_plan_id else None,
            # عمومی بدون پلن
            and_(
                CreditPricing.product_group_id == product_group_id,
                CreditPricing.operation_type == operation_type,
                CreditPricing.service_plan_id.is_(None),
                CreditPricing.applies_to_reseller_group_id.is_(None),
                CreditPricing.is_active == True
            ),
        ]

        # جستجو به ترتیب اولویت
        for query in queries:
            if query is None:
                continue
            pricing = db.query(CreditPricing).filter(query).first()
            if pricing:
                return pricing.credit_amount

        # اگر قیمت یافت نشد، از قیمت پایه پلن استفاده کن
        if service_plan_id:
            plan = db.query(ServicePlan).get(service_plan_id)
            if plan:
                return plan.credit_cost

        # اگر هیچ قیمتی یافت نشد
        raise ValueError(
            f"قیمتی برای عملیات {operation_type} در گروه محصول {product_group_id} یافت نشد"
        )

    @staticmethod
    def get_transactions(
        db: Session,
        reseller_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CreditTransaction]:
        """
        دریافت تراکنش‌ها

        Args:
            db: Database session
            reseller_id: فیلتر بر اساس نماینده (None = همه)
            limit: تعداد
            offset: offset

        Returns:
            List[CreditTransaction]: لیست تراکنش‌ها
        """
        query = db.query(CreditTransaction)

        if reseller_id:
            query = query.filter(CreditTransaction.reseller_id == reseller_id)

        query = query.order_by(CreditTransaction.created_at.desc())
        query = query.offset(offset).limit(limit)

        return query.all()
