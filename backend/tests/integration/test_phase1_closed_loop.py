from datetime import UTC, datetime
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio(loop_scope="module")


class TestPhase1ClosedLoop:
    async def test_user_registration_creates_profile_settings_wallet(self):
        from app.services.auth.passwords import PasswordService
        from app.services.auth.service import AuthService
        from app.services.auth.tokens import TokenService

        class FakeUser:
            def __init__(self, id, username, username_normalized, email, email_normalized):
                self.id = id
                self.username = username
                self.username_normalized = username_normalized
                self.email = email
                self.email_normalized = email_normalized
                self.status = "active"

        class FakeCredential:
            def __init__(self, user_id, password_hash):
                self.user_id = user_id
                self.password_hash = password_hash

        class FakeSession:
            def __init__(self, id, user_id):
                self.id = id
                self.user_id = user_id
                self.session_token_hash = "hash"
                self.refresh_token_hash = "hash"
                self.expires_at = datetime.now(UTC)
                self.revoked_at = None

        class FakeRepo:
            def __init__(self):
                self.users = {}
                self.credentials = {}
                self.sessions = {}
                self.profiles = {}
                self.settings = {}
                self.wallets = {}
                self.committed = False

            async def get_user_by_email(self, email):
                return None

            async def get_user_by_username(self, username):
                return None

            async def get_user_by_id(self, user_id):
                return self.users.get(user_id)

            async def create_user(self, **kw):
                user = FakeUser(id=uuid4(), **kw)
                self.users[user.id] = user
                return user

            async def create_auth_credential(self, **kw):
                cred = FakeCredential(**kw)
                self.credentials[kw["user_id"]] = cred
                return cred

            async def create_profile_for_user(self, **kw):
                self.profiles[kw["user_id"]] = True

            async def create_settings_for_user(self, **kw):
                self.settings[kw["user_id"]] = True

            async def create_wallet_for_user(self, **kw):
                self.wallets[kw["user_id"]] = True

            async def get_auth_credential(self, user_id):
                return self.credentials.get(user_id)

            async def create_auth_session(self, **kw):
                session = FakeSession(id=uuid4(), user_id=kw["user_id"])
                self.sessions[session.id] = session
                return session

            async def get_auth_session(self, session_id):
                return self.sessions.get(session_id)

            async def update_auth_session_tokens(self, **kw):
                pass

            async def revoke_auth_session(self, **kw):
                pass

            async def update_last_login(self, **kw):
                pass

            async def commit(self):
                self.committed = True

            async def rollback(self):
                pass

        repo = FakeRepo()
        token_svc = TokenService(
            secret_key="test-secret-key-for-testing-only",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
            algorithm="HS256",
        )
        service = AuthService(
            repository=repo,
            password_service=PasswordService(),
            token_service=token_svc,
        )

        result = await service.register(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
        )

        assert result.user.username == "testuser"
        assert result.tokens.access_token
        assert len(repo.profiles) == 1
        assert len(repo.settings) == 1
        assert len(repo.wallets) == 1
        assert repo.committed

    async def test_shop_purchase_deducts_balance_and_increments_inventory(self):
        from app.db.models.economy import ItemType, PurchaseStatus, QuotaType, TierRequired
        from app.services.shop.service import ShopService
        from app.services.wallet.service import WalletService

        class FakeOffer:
            def __init__(self):
                self.id = uuid4()
                self.item_code = "item_001"
                self.display_name = "Test Item"
                self.rarity = "common"
                self.price_asset_code = "COIN"
                self.price_amount = 100
                self.is_active = True
                self.active_from = None
                self.active_to = None
                self.purchase_limit_per_user = None
                self.quota_type = QuotaType.UNLIMITED
                self.max_capacity = None
                self.refill_days = None
                self.tier_required = TierRequired.FREE
                self.experiment_flag = None
                self.item_type = ItemType.TIME_TREASURE

        class FakeInventory:
            def __init__(self, user_id, item_code):
                self.user_id = user_id
                self.item_code = item_code
                self.quantity = 1
                self.updated_at = datetime.now(UTC)
                self.quota_max = None
                self.refill_days = None
                self.last_refill_at = None
                self.next_refill_at = None

        class FakePurchase:
            def __init__(self, **kw):
                self.id = uuid4()
                self.user_id = kw.get("user_id")
                self.offer_id = kw.get("offer_id")
                self.item_code = kw.get("item_code")
                self.price_asset_code = kw.get("price_asset_code")
                self.price_amount = kw.get("price_amount")
                self.status = kw.get("status", PurchaseStatus.COMPLETED)
                self.purchased_at = datetime.now(UTC)

        class FakeShopRepo:
            def __init__(self):
                self.offer = FakeOffer()
                self.inventories = {}
                self.purchases = {}
                self.committed = False

            async def list_active_offers(self):
                return [self.offer]

            async def get_offer(self, offer_id):
                return self.offer if offer_id == self.offer.id else None

            async def get_inventory(self, user_id):
                return [i for i in self.inventories.values() if i.user_id == user_id]

            async def upsert_inventory(
                self,
                user_id,
                item_code,
                quantity,
                quota_max=None,
                refill_days=None,
                is_auto_refill=False,
            ):
                key = (user_id, item_code)
                if key in self.inventories:
                    if is_auto_refill:
                        self.inventories[key].quantity = quota_max if quota_max else quantity
                    else:
                        self.inventories[key].quantity += quantity
                else:
                    self.inventories[key] = FakeInventory(user_id, item_code)
                return self.inventories[key]

            async def create_purchase_record(self, **kw):
                r = FakePurchase(**kw)
                self.purchases[r.id] = r
                return r

            async def get_purchase_by_idempotency_key(self, key):
                return None

            async def count_purchases_by_offer(self, user_id, offer_id):
                return 0

            async def commit(self):
                self.committed = True

            async def rollback(self):
                pass

        class FakeWalletRepo:
            def __init__(self):
                self.balance = 500

            async def get_balance(self, user_id, asset_code):
                return self.balance

            async def create_ledger_entry(self, **kw):
                self.balance += kw["delta"]

            async def get_ledger_by_idempotency_key(self, key):
                return None

        shop_repo = FakeShopRepo()
        wallet_repo = FakeWalletRepo()
        wallet_svc = WalletService(repository=wallet_repo)
        shop_svc = ShopService(repository=shop_repo, wallet_service=wallet_svc)

        user_id = uuid4()
        result = await shop_svc.purchase(
            user_id,
            type("P", (), {"offer_id": shop_repo.offer.id, "idempotency_key": None})(),
        )

        assert result.status == PurchaseStatus.COMPLETED
        assert wallet_repo.balance == 400
        assert (user_id, "item_001") in shop_repo.inventories
        assert shop_repo.committed

    async def test_leaderboard_aggregates_xp(self):
        from app.services.leaderboard.service import LeaderboardService

        class FakeRow:
            def __init__(self, user_id, display_name, total_xp):
                self.user_id = user_id
                self.display_name = display_name
                self.total_xp = total_xp

        class FakeViewerRow:
            def __init__(self, user_id, display_name, total_xp):
                self.user_id = user_id
                self.display_name = display_name
                self.total_xp = total_xp

        class FakeFocusRow:
            def __init__(self):
                self.document_id = uuid4()
                self.title = "Test Document"
                self.completed_runs = 5
                self.total_sum = 10
                self.correct_sum = 8

        class FakeRepo:
            async def get_global_leaderboard(self, limit, offset):
                return [
                    FakeRow(uuid4(), "User A", 1000),
                    FakeRow(uuid4(), "User B", 750),
                    FakeRow(uuid4(), "User C", 500),
                ]

            async def count_global_leaderboard_users(self):
                return 3

            async def get_user_total_xp(self, user_id):
                return FakeViewerRow(user_id, "Test User", 500)

            async def get_user_rank(self, user_id, total_xp):
                return 3

            async def get_daily_focus_documents(self, *, user_id, start_at, end_at, limit):
                return [FakeFocusRow()]

        service = LeaderboardService(repository=FakeRepo())
        test_user_id = uuid4()
        result = await service.get_global_leaderboard(user_id=test_user_id, limit=10)

        assert len(result.entries) == 3
        assert result.entries[0].total_xp == 1000
        assert result.entries[0].rank == 1
        assert result.entries[1].rank == 2
        assert result.entries[2].rank == 3
