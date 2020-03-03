#
# This file is part of FaceDancer.
#
# pylint: disable=unused-wildcard-import, wildcard-import

import asyncio

from .             import default_main

from ..future      import *
from ..classes.hid import KeyboardKeys


@use_inner_classes_automatically
class USBKeyboardDevice(USBDevice):
    """ Simple USB keyboard device. """

    name           : str = "USB keyboard device"
    product_string : str = "Non-suspicious Keyboard"


    class KeyboardConfiguration(USBConfiguration):
        """ Primary USB configuration: act as a keyboard. """


        class KeyboardInterface(USBInterface):
            """ Core HID interface for our keyboard. """

            name         : str = "USB keyboard interface"
            class_number : int = 3


            class KeyEventEndpoint(USBEndpoint):
                number        : int             = 3
                direction     : USBDirection    = USBDirection.IN
                transfer_type : USBTransferType = USBTransferType.INTERRUPT
                interval      : int             = 10


            #
            # Raw descriptors -- TODO: build these from their component parts.
            #


            class USBClassDescriptor(USBClassDescriptor):
                number      : int   =  USBDescriptorTypeNumber.HID
                raw         : bytes = b'\x09\x21\x10\x01\x00\x01\x22\x2b\x00'


            class ReportDescriptor(USBDescriptor):
                number      : int    = USBDescriptorTypeNumber.REPORT
                raw         : bytes = b'\x05\x01\x09\x06\xA1\x01\x05\x07\x19\xE0\x29\xE7\x15\x00\x25\x01\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x01\x19\x00\x29\x65\x15\x00\x25\x65\x75\x08\x95\x01\x81\x00\xC0'


            @class_request_handler(number=USBStandardRequests.GET_INTERFACE)
            @to_this_interface
            def handle_get_interface_request(self, request):
                # Silently stall GET_INTERFACE class requests.
                request.stall()


    def __post_init__(self):
        super().__post_init__()

        # Keep track of any pressed keys, and any pressed modifiers.
        self.active_keys = set()
        self.modifiers   = 0


    def _generate_hid_report(self) -> bytes:
        """ Generates a single HID report for the given keyboard state. """

        # If we have active keypresses, compose a set of scancodes from them.
        # TODO: use construct?
        scancodes = self.active_keys if self.active_keys else (0,)
        return bytes([self.modifiers, 0, *scancodes])



    def handle_data_requested(self, endpoint: USBEndpoint):
        """ Provide data once per host request. """
        report = self._generate_hid_report()
        endpoint.send(report)


    #
    # User-facing API.
    #


    def key_down(self, code):
        self.active_keys.add(code)


    def key_up(self, code):
        self.active_keys.remove(code)


    async def type_scancode(self, code, duration=0.1):
        self.key_down(code)
        await asyncio.sleep(duration)
        self.key_up(code)


    async def type_scancodes(self, *codes, duration=0.1):
        for code in codes:
            await self.type_scancode(code, duration=duration)


    async def type_letter(self, letter, duration=0.1):
        await self.type_scancode(KeyboardKeys.get_simple_code(letter))


    async def type_letters(self, *letters, duration=0.1):
        for letter in letters:
            await self.type_letter(letter, duration=duration)


    async def type_string(self, string, duration=0.1):
        for letter in string:
            await self.type_letter(letter, duration=duration)


if __name__ == "__main__":
    default_main(USBKeyboardDevice)
