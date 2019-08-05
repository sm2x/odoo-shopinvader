# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import CommonCarrierCase


class CarrierCase(CommonCarrierCase):
    def test_available_carriers(self):
        response = self.service.dispatch("get_delivery_methods")
        self.assertEqual(len(response), 2)

    def test_setting_free_carrier(self):
        cart = self._set_carrier(self.free_carrier)
        self.assertEqual(cart["shipping"]["amount"]["total"], 0)

    def test_setting_poste_carrier(self):
        cart = self._set_carrier(self.poste_carrier)
        # Check shipping amount
        cart_ship = cart.get("shipping")
        self.assertEqual(cart_ship["amount"]["total"], 20)
        self.assertEqual(cart_ship["amount"]["untaxed"], 17.39)
        self.assertEqual(cart_ship["amount"]["tax"], 2.61)

        # Check items amount
        self.assertEqual(cart["lines"]["amount"]["total"], 8555.0)
        self.assertEqual(cart["lines"]["amount"]["untaxed"], 8555.0)
        self.assertEqual(cart["lines"]["amount"]["tax"], 0)

        # Check total amount
        self.assertEqual(cart["amount"]["total"], 8575.0)
        self.assertEqual(cart["amount"]["untaxed"], 8572.39)
        self.assertEqual(cart["amount"]["tax"], 2.61)

        # Check totals without shipping prices
        cart_amount = cart.get("amount")
        total_without_shipping = (
            cart_amount["total"] - cart_ship["amount"]["total"]
        )
        untaxed_without_shipping = (
            cart_amount["untaxed"] - cart_ship["amount"]["untaxed"]
        )
        tax_without_shipping = cart_amount["tax"] - cart_ship["amount"]["tax"]
        self.assertEqual(
            cart_amount["total_without_shipping"], total_without_shipping
        )
        self.assertEqual(
            cart_amount["untaxed_without_shipping"], untaxed_without_shipping
        )
        self.assertEqual(
            cart_amount["tax_without_shipping"], tax_without_shipping
        )

    def test_reset_carrier_on_add_item(self):
        self._apply_carrier_and_assert_set()
        cart = self.add_item(self.product_1.id, 2)
        self.assertEqual(cart["shipping"]["amount"]["total"], 0)
        self.assertFalse(cart["shipping"]["selected_carrier"])

    def test_reset_carrier_on_update_item(self):
        cart = self._apply_carrier_and_assert_set()
        items = cart["lines"]["items"]
        cart = self.update_item(items[0]["id"], 1)
        self.assertEqual(cart["shipping"]["amount"]["total"], 0)
        self.assertFalse(cart["shipping"]["selected_carrier"])

    def test_reset_carrier_on_delte_item(self):
        cart = self._apply_carrier_and_assert_set()
        items = cart["lines"]["items"]
        cart = self.delete_item(items[0]["id"])
        self.assertEqual(cart["shipping"]["amount"]["total"], 0)
        self.assertFalse(cart["shipping"]["selected_carrier"])
