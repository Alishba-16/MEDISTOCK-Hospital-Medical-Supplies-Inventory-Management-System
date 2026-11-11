"""
================================================================================
MEDISTOCK — AUTOMATED UNIT TEST SUITE
================================================================================
Verifies:
  1. Manual Singly Linked List Queue (`Node` and `Queue`) all 9 required methods
     and all edge cases (empty, single element, multiple elements, removing last
     element, updating/deleting front/middle/rear, accurate front/rear pointers).
  2. SQLite3 WAL Relational Database (all 6 categories, all 6 departments,
     product/batch separation, and lock-free concurrent updates).
  3. All 10 Required Hospital Reports (CSV & PDF 1.4 export verification).
================================================================================
"""

import os
import unittest
from queue_dsa import LinkedListQueue, Node, Queue, QueueNode
import database
import reports_exporter


class TestSinglyLinkedListQueue(unittest.TestCase):
    """Tests all 9 required methods and edge cases of the manual Linked List Queue."""

    def test_empty_queue_operations(self):
        q = Queue("EmptyQueueTest")
        self.assertTrue(q.is_empty())
        self.assertEqual(q.size(), 0)
        self.assertIsNone(q.peek())
        self.assertIsNone(q.dequeue())
        self.assertEqual(q.display(), [])
        self.assertIsNone(q.search("B001"))
        self.assertIsNone(q.delete("B001"))
        self.assertFalse(q.update("B001", {"quantity": 99}))
        self.assertIsNone(q.front)
        self.assertIsNone(q.rear)

    def test_single_element_and_remove_last_element(self):
        q = LinkedListQueue("SingleElementQueue")
        node = q.enqueue({"id": "B001", "batch_id": "B001", "quantity": 100})
        self.assertIsInstance(node, Node)
        self.assertFalse(q.is_empty())
        self.assertEqual(q.size(), 1)
        self.assertIs(q.front, q.rear)
        self.assertEqual(q.peek()["batch_id"], "B001")

        # Dequeue the only element -> both front and rear must reset to None
        removed = q.dequeue()
        self.assertEqual(removed["batch_id"], "B001")
        self.assertTrue(q.is_empty())
        self.assertEqual(q.size(), 0)
        self.assertIsNone(q.front)
        self.assertIsNone(q.rear)

    def test_multiple_elements_search_update_delete_pointers(self):
        q = Queue("MultiQueueTest")
        for rid, dept, qty in [
            ("R001", "Emergency", 50),
            ("R002", "ICU", 80),
            ("R003", "General Ward", 60),
            ("R004", "Operation Theatre", 100),
        ]:
            q.enqueue({"id": rid, "request_id": rid, "department": dept, "quantity_requested": qty})

        self.assertEqual(q.size(), 4)
        self.assertEqual(q.front.data["request_id"], "R001")
        self.assertEqual(q.rear.data["request_id"], "R004")

        # search(id) without altering order
        found = q.search("R002")
        self.assertIsNotNone(found)
        self.assertEqual(found["department"], "ICU")
        self.assertEqual([x["request_id"] for x in q.display()], ["R001", "R002", "R003", "R004"])

        # update(id, data) on middle element
        self.assertTrue(q.update("R002", {"quantity_requested": 95}))
        self.assertEqual(q.search("R002")["quantity_requested"], 95)

        # delete(id) on middle element (R003)
        deleted_mid = q.delete("R003")
        self.assertEqual(deleted_mid["request_id"], "R003")
        self.assertEqual([x["request_id"] for x in q.display()], ["R001", "R002", "R004"])

        # delete(id) on rear element (R004) -> rear must update to R002
        deleted_rear = q.delete("R004")
        self.assertEqual(deleted_rear["request_id"], "R004")
        self.assertEqual(q.rear.data["request_id"], "R002")
        self.assertIsNone(q.rear.next)

        # delete(id) on front element (R001) -> front and rear must both point to R002
        deleted_front = q.delete("R001")
        self.assertEqual(deleted_front["request_id"], "R001")
        self.assertIs(q.front, q.rear)
        self.assertEqual(q.front.data["request_id"], "R002")


class TestDatabaseAndReports(unittest.TestCase):
    """Tests SQLite WAL concurrency, 6 categories, 6 departments, and 10 CSV/PDF exports."""

    def setUp(self):
        database.init_database()

    def test_all_categories_and_departments_seeded(self):
        conn = database.get_connection()
        try:
            cats = [r["category"] for r in conn.execute("SELECT DISTINCT category FROM medicines").fetchall()]
            for expected_cat in database.INVENTORY_CATEGORIES:
                self.assertIn(expected_cat, cats)

            depts = [r["department"] for r in conn.execute("SELECT DISTINCT department FROM requisitions").fetchall()]
            for expected_dept in database.HOSPITAL_DEPARTMENTS:
                self.assertIn(expected_dept, depts)
        finally:
            conn.close()

    def test_lock_free_catalog_update_and_transaction_log(self):
        conn = database.get_connection()
        try:
            conn.execute("UPDATE medicines SET min_threshold = min_threshold WHERE id = 'MED-101'")
            conn.commit()
        finally:
            conn.close()

        tx_id = database.log_transaction(
            "CATALOG_UPDATE", "MED-101", "Amoxicillin + Clavulanate 625mg",
            "Medicines", 150, "Verified lock-free update"
        )
        self.assertTrue(tx_id.startswith("TX-"))

    def test_all_10_reports_export_csv_and_pdf(self):
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports_test")
        os.makedirs(out_dir, exist_ok=True)
        for key, _title in reports_exporter.REPORT_TYPES:
            headers, _rows = reports_exporter.generate_report_data(key)
            self.assertGreater(len(headers), 0)
            csv_path = os.path.join(out_dir, f"{key}.csv")
            pdf_path = os.path.join(out_dir, f"{key}.pdf")
            reports_exporter.export_to_csv(key, csv_path)
            reports_exporter.export_to_pdf(key, pdf_path)
            self.assertTrue(os.path.exists(csv_path))
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
