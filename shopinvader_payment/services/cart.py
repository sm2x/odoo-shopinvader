# -*- coding: utf-8 -*-
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class CartService(Component):
    _inherit = 'shopinvader.cart.service'

    # Public service

    def add_payment(self, **params):
        cart = self._get()
        if not cart:
            raise UserError(_('There is not cart'))
        else:
            self._set_payment_mode(cart, params)
            provider_name = cart.payment_mode_id.provider
            if provider_name:
                return self._process_payment_provider(
                    provider_name, cart, params[provider_name])
            else:
                return self._confirm_cart(cart)

    def check_payment(self, provider_name=None, **params):
        with self.env['gateway.transaction']._get_provider(provider_name)\
                as provider:
            transaction = provider._get_transaction_from_return(params)
            transaction.check_state()
            if transaction.state in ['to_capture', 'succeeded']:
                result = self.update(
                    step={'next': self.locomotive_backend.last_step_id.code},
                    )
                result['redirect_to'] = transaction.redirect_success_url
                return result
            else:
                return {
                    'redirect_to': transaction.redirect_cancel_url,
                    'store_cache': {
                        'notifications': [{
                            'type': 'danger',
                            'message': _('Payment failed please retry'),
                        }]
                    }
                }
        _logger.error('Shopinvader: Transaction params are invalid')
        return {'redirect_to': self.locomotive_backend.location}

    # Validator
    def _validator_add_payment(self):
        validator = {
            'payment_mode': {
                'type': 'dict',
                'schema': {
                    'id': {
                        'coerce': int,
                        'nullable': True,
                        'required': True,
                        },
                    }
                },
            }
        for provider in self.env['gateway.transaction']._get_all_provider():
            if hasattr(provider, '_validator_add_payment'):
                validator[provider._usage] = {
                    'type': 'dict',
                    'schema': provider._validator_add_payment()
                    }
        return validator

    def _validator_check_payment(self):
        validator = {
            'provider_name': {
                'type': 'string',
                'required': True,
                }
            }
        for provider in self.env['gateway.transaction']._get_all_provider():
            if hasattr(provider, '_validator_check_payment'):
                validator.update(provider._validator_check_payment())
        return validator

    # Private method
    def _set_payment_mode(self, cart, params):
        payment_mode_id = params['payment_mode']['id']
        available_payment_mode_ids = [
            x['id'] for x in self._get_available_payment_mode()]
        if payment_mode_id not in available_payment_mode_ids:
            raise UserError(_('Unsupported payment mode'))
        else:
            vals = cart.play_onchanges({
                'payment_mode_id': payment_mode_id,
                }, ['payment_mode_id'],
                )
            cart.write(vals)
        return cart.payment_mode_id.provider

    def _process_payment_provider(self, provider_name, cart, params):
        params['return_url'] = "%s/%s/%s" % (
            self.locomotive_backend.location,
            '_store/cart/check_payment',
            provider_name)
        transaction = self.env['gateway.transaction'].generate(
            provider_name, cart, **params)
        if transaction.url:
            return {'redirect_to': transaction.url}
        elif transaction.state in ('succeeded', 'to_capture'):
            return self._confirm_cart(cart)
        else:
            raise UserError(_('Payment failed please retry'))

    def _to_json(self, cart):
        res = super(CartService, self)._to_json(cart)
        if cart:
            res.update({
                'available_payment_method_ids':
                    self._get_available_payment_mode(),
            })
        return res

    def _prepare_payment(self, method):
        return {
            'id': method.payment_mode_id.id,
            'name': method.payment_mode_id.name,
            'code': method.code,
            'description': method.description,
            }

    def _get_available_payment_mode(self):
        methods = []
        for method in self.locomotive_backend.payment_method_ids:
            methods.append(self._prepare_payment(method))
        return methods
