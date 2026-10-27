"""Boshqaruv buyruqlari.

  python -m app.cli create-user --username ali [--email a@b.uz]
      Parol: SUVNAZORAT_PASSWORD env yoki terminalda yashirin so'raladi.
  python -m app.cli seed-rules
"""
import argparse
import getpass
import os
import sys

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.db.seed_rules import SEED_RULES
from app.db.session import session_scope
from app.models.enums import MatchType
from app.schemas.rule import RuleCreate
from app.services import audit, auth_service, rules_service


def cmd_create_user(args: argparse.Namespace) -> int:
    password = os.environ.get("SUVNAZORAT_PASSWORD")
    if not password:
        password = getpass.getpass("Parol (kamida 12 belgi): ")
        if password != getpass.getpass("Parolni takrorlang: "):
            print("Parollar mos kelmadi.", file=sys.stderr)
            return 1
    with session_scope() as db:
        try:
            user = auth_service.create_user(db, args.username, password, args.email)
            audit.log_action(db, user_id=None, action="user.create_cli", entity_type="user",
                             entity_id=user.id)
            db.commit()
        except ValueError as exc:
            print(f"Xato: {exc}", file=sys.stderr)
            return 1
        except IntegrityError:
            db.rollback()
            print("Xato: bunday login yoki email allaqachon mavjud.", file=sys.stderr)
            return 1
        print(f"Foydalanuvchi yaratildi: {user.username} (id={user.id})")
    return 0


def cmd_seed_rules(_: argparse.Namespace) -> int:
    added = skipped = 0
    with session_scope() as db:
        for name, keyword, category, priority in SEED_RULES:
            try:
                rules_service.create_rule(
                    db,
                    RuleCreate(name=name, keyword=keyword, category=category,
                               match_type=MatchType.PHRASE, priority=priority),
                    None,
                )
                added += 1
            except AppError:  # normalizatsiyadan keyin takror (masalan, apostrof varianti)
                db.rollback()
                skipped += 1
    print(f"Qo'shildi: {added}, takror sifatida o'tkazib yuborildi: {skipped}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    cu = sub.add_parser("create-user")
    cu.add_argument("--username", required=True)
    cu.add_argument("--email")
    cu.set_defaults(func=cmd_create_user)
    sr = sub.add_parser("seed-rules")
    sr.set_defaults(func=cmd_seed_rules)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
