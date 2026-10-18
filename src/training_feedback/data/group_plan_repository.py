"""V3 normalized day/item/member/set persistence; application owns transactions."""

import json
from uuid import uuid4

from .conversion_repository import ConversionRepository


class GroupPlanRepository:
    def __init__(self, connection):
        self.connection = connection

    def edit_documents(self):
        return [self.edit_document(row[0]) for row in self.connection.execute(
            "SELECT id FROM plan_edit_document ORDER BY created_at,id"
        )]

    def edit_document(self, identifier):
        row = self.connection.execute(
            "SELECT * FROM plan_edit_document WHERE id=?", (identifier,),
        ).fetchone()
        if row is None:
            raise ValueError("没有找到草稿编辑文档。")
        document = dict(row)
        if document["format_version"] != 2:
            raise ValueError("草稿格式不受支持，请使用支持此格式的程序版本。")
        document["payload"] = json.loads(document.pop("payload_json"))
        return document

    def document_for_revision(self, revision_id):
        row = self.connection.execute(
            "SELECT id FROM plan_edit_document WHERE revision_id=?", (revision_id,),
        ).fetchone()
        return self.edit_document(row[0]) if row else None

    def put_document(self, payload, now, *, identifier=None, expected_token=None,
                     purpose="new", revision_id=None, source_revision_id=None,
                     requested_base_number=None):
        raw = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        if identifier is None:
            identifier = "draft." + uuid4().hex
            self.connection.execute(
                "INSERT INTO plan_edit_document(id,format_version,purpose,revision_id,"
                "source_revision_id,requested_base_number,payload_json,created_at,updated_at) "
                "VALUES (?,2,?,?,?,?,?,?,?)",
                (identifier, purpose, revision_id, source_revision_id, requested_base_number,
                 raw, now, now),
            )
        else:
            cursor = self.connection.execute(
                "UPDATE plan_edit_document SET payload_json=?,updated_at=?,requested_base_number=?,"
                "edit_token=edit_token+1 WHERE id=? AND edit_token=?",
                (raw, now, requested_base_number, identifier, expected_token),
            )
            if cursor.rowcount != 1:
                raise ValueError("草稿已被修改，请重新打开后继续；本次输入尚未保存。")
        return identifier

    def link_document(self, identifier, revision_id):
        self.connection.execute(
            "UPDATE plan_edit_document SET revision_id=? WHERE id=?", (revision_id, identifier),
        )

    def delete_document(self, identifier, expected_token):
        cursor = self.connection.execute(
            "DELETE FROM plan_edit_document WHERE id=? AND edit_token=?",
            (identifier, expected_token),
        )
        if cursor.rowcount != 1:
            raise ValueError("草稿已被修改，请重新打开后继续。")

    def delete_draft_revision(self, identifier):
        current = self.get(identifier)
        if current["status"] != "draft":
            raise ValueError("只能删除草稿；已启用版本和历史版本须保留。")
        if current["import"] or current["conversion_registrations"] or self.connection.execute(
            "SELECT 1 FROM group_plan_export WHERE revision_id=?", (identifier,),
        ).fetchone():
            raise ValueError("此草稿关联导入原件或已导出证据，须保留来源记录，不能删除。")
        self.connection.execute(
            "DELETE FROM group_plan_set WHERE item_id IN "
            "(SELECT id FROM group_plan_item WHERE revision_id=?)", (identifier,))
        self.connection.execute("DELETE FROM group_plan_item WHERE revision_id=? AND parent_id "
                                "IS NOT NULL", (identifier,))
        self.connection.execute("DELETE FROM group_plan_item WHERE revision_id=?", (identifier,))
        self.connection.execute("DELETE FROM group_plan_day WHERE revision_id=?", (identifier,))
        self.connection.execute("DELETE FROM group_plan_revision WHERE id=?", (identifier,))
        self.connection.execute("DELETE FROM group_plan WHERE id=? AND active_revision_id IS NULL "
                                "AND NOT EXISTS(SELECT 1 FROM group_plan_revision WHERE plan_id=?)",
                                (current["plan_id"], current["plan_id"]))

    def list_plans(self):
        return [
            dict(row) for row in self.connection.execute("SELECT * FROM group_plan ORDER BY id")
        ]

    def revisions(self, plan_id):
        return [
            self.get(row[0])
            for row in self.connection.execute(
                "SELECT id FROM group_plan_revision WHERE plan_id=? ORDER BY revision_number",
                (plan_id,),
            )
        ]

    def get(self, identifier):
        row = self.connection.execute(
            "SELECT * FROM group_plan_revision WHERE id=?",
            (identifier,),
        ).fetchone()
        if row is None:
            raise ValueError("Plan revision was not found.")
        revision = dict(row)
        revision["migration"] = json.loads(revision.pop("migration_json") or "null")
        revision["base_number"] = self.connection.execute(
            "SELECT base_number FROM group_plan WHERE id=?", (row["plan_id"],)
        ).fetchone()[0]
        plan = {"name": row["name"], "purpose": row["purpose"], "days": []}
        for day in self.connection.execute(
            "SELECT * FROM group_plan_day WHERE revision_id=? ORDER BY day_order",
            (identifier,),
        ):
            items = [
                self._item(item)
                for item in self.connection.execute(
                    "SELECT * FROM group_plan_item WHERE day_id=? AND parent_id IS NULL "
                    "ORDER BY item_order",
                    (day["id"],),
                )
            ]
            plan["days"].append({"order": day["day_order"], "items": items})
        revision["payload"] = {
            "schema": "training_feedback.plan",
            "schema_version": row["format_version"],
            "intent": "new",
            "rationale": row["rationale"],
            "change_description": row["change_description"],
            "plan_code": row["plan_code"],
            "plan": plan,
        }
        source = json.loads(revision.pop("source_json"))
        if source is not None:
            revision["payload"]["source"] = source
        imported = self.connection.execute(
            "SELECT * FROM group_plan_import WHERE revision_id=?",
            (identifier,),
        ).fetchone()
        revision["import"] = dict(imported) if imported else None
        revision["conversion_registrations"] = ConversionRepository(
            self.connection).registrations(revision_id=identifier)
        revision["pins"] = [
            {**dict(pin), "review": json.loads(pin["review_json"])}
            for pin in self.connection.execute(
                "SELECT p.*, i.item_key FROM group_plan_pin p JOIN group_plan_item i "
                "ON i.id=p.item_id WHERE i.revision_id=? ORDER BY i.id",
                (identifier,),
            )
        ]
        return revision

    def _item(self, row):
        item = json.loads(row["fields_json"])
        item.update(item_id=row["item_key"], order=row["item_order"])
        if row["kind"] == "group":
            item["members"] = [
                self._item(member)
                for member in self.connection.execute(
                    "SELECT * FROM group_plan_item WHERE parent_id=? ORDER BY item_order",
                    (row["id"],),
                )
            ]
        else:
            item["sets"] = [
                {
                    "order": dose["set_order"],
                    "value": dose["value"],
                    "unit": dose["unit"],
                    "per_side": bool(dose["per_side"]),
                    "note": dose["note"],
                    "rest_after_set_seconds": dose["rest_after_set_seconds"],
                }
                for dose in self.connection.execute(
                    "SELECT * FROM group_plan_set WHERE item_id=? ORDER BY set_order",
                    (row["id"],),
                )
            ]
        return item

    def create(self, payload, now, plan_id=None, *, base_number=None, plan_code=None,
               change_description="", upgrade_source_revision_id=None):
        plan = payload["plan"]
        if plan_id is None:
            if base_number is None:
                used = {
                    row[0] for row in self.connection.execute(
                        "SELECT base_number FROM group_plan"
                    )
                }
                base_number = next(
                    (number for number in range(1, 1000) if number not in used), None
                )
            if type(base_number) is not int or not 1 <= base_number <= 999:
                raise ValueError("A plan base number must be between 001 and 999.")
            plan_id = self.connection.execute(
                "INSERT INTO group_plan(base_number,name,created_at) VALUES (?,?,?)",
                (base_number, plan["name"], now),
            ).lastrowid
        elif (
            self.connection.execute(
                "SELECT 1 FROM group_plan WHERE id=?",
                (plan_id,),
            ).fetchone()
            is None
        ):
            raise ValueError("Target plan was not found.")
        elif plan_code is None:
            raise ValueError("A revision code must be assigned for an existing plan.")
        number = self.connection.execute(
            "SELECT COALESCE(MAX(revision_number),0)+1 FROM group_plan_revision WHERE plan_id=?",
            (plan_id,),
        ).fetchone()[0]
        if plan_code is None:
            base = self.connection.execute(
                "SELECT base_number FROM group_plan WHERE id=?", (plan_id,)
            ).fetchone()[0]
            plan_code = f"plan-{base:03d}.01.00"
        identifier = self.connection.execute(
            "INSERT INTO group_plan_revision(plan_id,revision_number,status,name,purpose,"
            "plan_code,change_description,upgrade_source_revision_id,target_plan_name,"
            "rationale,source_json,created_at) VALUES (?,?,'draft',?,?,?,?,?,?,?,?,?)",
            (
                plan_id,
                number,
                plan["name"],
                plan["purpose"],
                plan_code,
                change_description,
                upgrade_source_revision_id,
                plan.get("target_plan_name"),
                payload["rationale"],
                json.dumps(payload.get("source")),
                now,
            ),
        ).lastrowid
        self.connection.execute("UPDATE group_plan_revision SET format_version=? WHERE id=?",
                                (payload["schema_version"], identifier))
        self._children(identifier, plan)
        return identifier

    def replace(self, identifier, payload, expected_token, *, plan_code=None,
                change_description=None):
        current = self.get(identifier)
        if current["status"] != "draft":
            raise ValueError("Only draft revisions can be edited.")
        if current["edit_token"] != expected_token:
            raise ValueError("The displayed plan revision changed.")
        self.connection.execute(
            "DELETE FROM group_plan_set WHERE item_id IN "
            "(SELECT id FROM group_plan_item WHERE revision_id=?)",
            (identifier,),
        )
        self.connection.execute(
            "DELETE FROM group_plan_item WHERE revision_id=? AND parent_id IS NOT NULL",
            (identifier,),
        )
        self.connection.execute("DELETE FROM group_plan_item WHERE revision_id=?", (identifier,))
        self.connection.execute("DELETE FROM group_plan_day WHERE revision_id=?", (identifier,))
        plan = payload["plan"]
        self.connection.execute(
            "UPDATE group_plan_revision SET name=?,purpose=?,target_plan_name=?,rationale=?,"
            "source_json=?,plan_code=?,change_description=?,edit_token=edit_token+1 WHERE id=?",
            (
                plan["name"],
                plan["purpose"],
                plan.get("target_plan_name"),
                payload["rationale"],
                json.dumps(payload.get("source")),
                plan_code or current["plan_code"],
                current["change_description"] if change_description is None else change_description,
                identifier,
            ),
        )
        self._children(identifier, plan)

        self.connection.execute("UPDATE group_plan_revision SET format_version=? WHERE id=?",
                                (payload["schema_version"], identifier))

    def _children(self, identifier, plan):
        for day in plan["days"]:
            day_id = self.connection.execute(
                "INSERT INTO group_plan_day(revision_id,day_order) VALUES (?,?)",
                (identifier, day["order"]),
            ).lastrowid
            for item in day["items"]:
                parent = self._insert_item(identifier, day_id, item, None)
                for member in item.get("members", []):
                    self._insert_item(identifier, day_id, member, parent)

    def _insert_item(self, revision_id, day_id, item, parent):
        fields = {
            key: value
            for key, value in item.items()
            if key not in {"item_id", "order", "sets", "members"}
        }
        identifier = self.connection.execute(
            "INSERT INTO group_plan_item(revision_id,day_id,parent_id,item_key,item_order,kind,"
            "fields_json) VALUES (?,?,?,?,?,?,?)",
            (
                revision_id,
                day_id,
                parent,
                item["item_id"],
                item["order"],
                "member" if parent is not None else item["kind"],
                json.dumps(fields, ensure_ascii=False),
            ),
        ).lastrowid
        for dose in item.get("sets", []):
            self.connection.execute(
                "INSERT INTO group_plan_set(item_id,set_order,value,unit,per_side,note,"
                "rest_after_set_seconds) VALUES (?,?,?,?,?,?,?)",
                (
                    identifier,
                    dose["order"],
                    dose["value"],
                    dose["unit"],
                    int(dose["per_side"]),
                    dose["note"],
                    dose["rest_after_set_seconds"],
                ),
            )
        return identifier

    def active(self, plan_id):
        row = self.connection.execute(
            "SELECT active_revision_id FROM group_plan WHERE id=?",
            (plan_id,),
        ).fetchone()
        return self.get(row[0]) if row and row[0] else None

    def find_plan(self, name):
        row = self.connection.execute("SELECT id FROM group_plan WHERE name=?", (name,)).fetchone()
        return row[0] if row else None

    def find_base_number(self, base_number):
        row = self.connection.execute(
            "SELECT id FROM group_plan WHERE base_number=?", (base_number,)
        ).fetchone()
        return row[0] if row else None

    def upgrade_draft(self, plan_id, source_revision_id):
        row = self.connection.execute(
            "SELECT id FROM group_plan_revision WHERE plan_id=? AND status='draft' "
            "AND upgrade_source_revision_id=? ORDER BY revision_number DESC LIMIT 1",
            (plan_id, source_revision_id),
        ).fetchone()
        return self.get(row[0]) if row else None

    def pin(self, revision_id, item_key, content_id, review, now):
        item_id = self.connection.execute(
            "SELECT id FROM group_plan_item WHERE revision_id=? AND item_key=?",
            (revision_id, item_key),
        ).fetchone()[0]
        self.connection.execute(
            "INSERT INTO group_plan_pin VALUES (?,?,?,?)",
            (item_id, content_id, json.dumps(review, ensure_ascii=False), now),
        )

    def activate(self, identifier, now):
        current = self.get(identifier)
        self.connection.execute(
            "UPDATE group_plan_revision SET status='superseded' "
            "WHERE plan_id=? AND status='active'",
            (current["plan_id"],),
        )
        self.connection.execute(
            "UPDATE group_plan_revision SET status='active',activated_at=? WHERE id=?",
            (now, identifier),
        )
        self.connection.execute(
            "UPDATE group_plan SET active_revision_id=?,name=? WHERE id=?",
            (identifier, current["name"], current["plan_id"]),
        )

    def register_import(self, identifier, relative, digest, original, now):
        self.connection.execute(
            "INSERT INTO group_plan_import(revision_id,source_path,sha256,"
            "original_payload,imported_at) "
            "VALUES (?,?,?,?,?)",
            (identifier, relative, digest, original, now),
        )

    def check_source(self, source):
        for field, table in (
            ("session_id", "group_session"),
            ("export_id", "group_plan_export"),
        ):
            if (
                source.get(field) is not None
                and self.connection.execute(
                    f"SELECT 1 FROM {table} WHERE id=?",
                    (source[field],),
                ).fetchone()
                is None
                and not (field == "export_id" and self.connection.execute(
                    "SELECT 1 FROM conversion_registration WHERE kind='export' AND id=?",
                    (source[field],),
                ).fetchone())
            ):
                raise ValueError("External source does not belong to this data root.")

    def schema_version(self):
        return self.connection.execute("SELECT MAX(version) FROM schema_migration").fetchone()[0]

    def register_export(self, identifier, directory, now):
        reserved = self.connection.execute(
            "SELECT COALESCE(MAX(id),0) FROM conversion_registration WHERE kind='export'"
        ).fetchone()[0]
        maximum = self.connection.execute(
            "SELECT COALESCE(MAX(id),0) FROM group_plan_export"
        ).fetchone()[0]
        return self.connection.execute(
            "INSERT INTO group_plan_export(id,revision_id,directory,created_at) VALUES (?,?,?,?)",
            (max(reserved, maximum) + 1, identifier, directory, now),
        ).lastrowid
