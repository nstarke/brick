from bip.base import *
from bip.hexrays import *

from ..base_module import BaseModule

from .uefi.bs import EfiBootServices
from .uefi.rt import EfiRuntimeServices
from .uefi.smm.cpu import SmmCpuCallsFactory
from .uefi.smm.access2 import SmmAccess2Protocol
from .uefi.smm.smst import SmstFactory

from ...utils import bip_utils

class PostprocessorModule(BaseModule):

    EFI_SMM_HANDLER_ENTRY_POINT = BipType.from_c("""EFI_STATUS (f)(
        EFI_HANDLE DispatchHandle,
        void * Context,
        EFI_SMM_SW_CONTEXT * CommBuffer,
        UINTN * CommBufferSize)""")

    def _fix_sw_smis_signatures(self):
        for sw_smi_handler in BipFunction.get_by_prefix("SwSmiHandler"):
            self.EFI_SMM_HANDLER_ENTRY_POINT.set_at(sw_smi_handler.ea)

    def _fix_efi_services_signatures(self):

        SmstFactory.process_calls()
        EfiBootServices.process_calls()
        EfiRuntimeServices.process_calls()
        SmmCpuCallsFactory.process_calls()
        SmmAccess2Protocol.process_calls()

    def _rename_enums(self):
        idc.import_type(-1, 'MACRO_EFI')
        me = BipEnum.get('MACRO_EFI')

        for ins in BipInstr.iter_all():
            for (op_id, op) in enumerate(ins.ops):
                if op.type == BipOpType.IMM and op.value & 0x8000000000000000:
                    idc.op_enum(ins.ea, op_id, me._eid, 0)

    def _handle_assignments(self):

        def callback(node: CNode):
            assert isinstance(node, CNodeExprAsg)

            src = node.src.ignore_cast
            dst = node.dst.ignore_cast

            # Check that both objects are globals
            if isinstance(src, CNodeExprObj) and isinstance(dst, CNodeExprObj):
                # The destination operand is merely an integer.
                if isinstance(dst.type, BTypeInt):
                    # The source is a pointer to a structure.
                    if isinstance(src.type, BTypePtr) and isinstance(src.type.pointed, BTypeStruct):
                        # Copy type.
                        src.type.set_at(dst.value)
                        node.hxcfunc.invalidate_cache()
                        return True

        modified = bip_utils.collect_cnode_filterlist(None, callback, [CNodeExprAsg])
        while modified:
            modified = bip_utils.collect_cnode_filterlist(None, callback, [CNodeExprAsg])

    def run(self):
        # Handle assigment of global variables.
        self._handle_assignments()
        # Apply correct signature to all SW SMI handlers.
        self._fix_sw_smis_signatures()
        # Fix signatures for common EFI/SMM services that efiXplorer missed.
        self._fix_efi_services_signatures()
        # Rename EFI status codes.
        self._rename_enums()