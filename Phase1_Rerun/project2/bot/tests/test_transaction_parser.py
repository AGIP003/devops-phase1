import unittest

from bot.transaction_parser import TransactionInputError, parse_transaction


class TransactionParserTests(unittest.TestCase):
    def test_infers_transport_and_default_payment(self):
        result = parse_transaction("250 matatu fare", {})
        self.assertEqual(result["category"], "transport")
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["payment_method"], "m-pesa")

    def test_parses_currency_and_payment_alias(self):
        result = parse_transaction(
            "KES 1,200 groceries via mpesa",
            {"default_payment_method": "cash"},
        )
        self.assertEqual(result["amount"], 1200)
        self.assertEqual(result["category"], "groceries")
        self.assertEqual(result["payment_method"], "m-pesa")
        self.assertEqual(result["description"], "groceries via mpesa")
        self.assertFalse(result["invalid_payment"])

    def test_invalid_explicit_payment_requests_choice(self):
        result = parse_transaction("1200 groceries via bitcoin", {})
        self.assertEqual(result["category"], "groceries")
        self.assertIsNone(result["payment_method"])
        self.assertTrue(result["invalid_payment"])
        self.assertEqual(result["supplied_payment"], "bitcoin")

    def test_negative_amount_indicates_income(self):
        result = parse_transaction("-5000 freelance payment", {})
        self.assertEqual(result["amount"], 5000)
        self.assertEqual(result["type"], "income")
        self.assertEqual(result["category"], "freelance")

    def test_custom_alias(self):
        result = parse_transaction(
            "800 kinyozi",
            {"category_aliases": {"kinyozi": "personal care"}},
        )
        self.assertEqual(result["category"], "personal care")

    def test_vague_positive_input_requests_expense_choice(self):
        result = parse_transaction("400 weekend thing", {})
        self.assertTrue(result["ambiguous"])
        self.assertTrue(all(item["type"] == "expense" for item in result["candidates"]))

    def test_description_is_required(self):
        with self.assertRaises(TransactionInputError):
            parse_transaction("250", {})


if __name__ == "__main__":
    unittest.main()
