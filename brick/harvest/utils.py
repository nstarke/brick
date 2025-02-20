from logger import log_operation, log_warning
import os
import shutil
from .NativePythonHarvester import NativePythonHarvester
from .UefiToolHarvester import UefiToolHarvester
from .SingleFileHarvester import SingleFileHarvester
from .DirectoryHarvester import DirectoryHarvester

def do_harvest(rom, outdir, guids_dict=None, filter=None):
    log_operation(f'Creating directory {outdir}')

    if os.path.exists(outdir):
        shutil.rmtree(outdir)

    os.mkdir(outdir)

    for cls in (NativePythonHarvester, UefiToolHarvester, DirectoryHarvester, SingleFileHarvester):
        log_operation(f"Trying to harvest SMM modules using '{cls.__name__}'")

        try:
            harvester = cls()
            harvester.ext = 'efi'
            harvester.guids_dict = guids_dict
            if filter is not None:
                harvester.filter = filter
            harvester.harvest(rom, outdir)
        except Exception as e:
            # Harvest was unsuccessful, fall back into other harvesters in case there are any.
            log_warning(f"Harvest of SMM modules using '{cls.__name__}' failed, {e}")
            continue

        if os.listdir(outdir):
            # Harvest was successful.
            break
        else:
            # Harvest was unsuccessful, fall back into other harvesters in case there are any.
            log_warning(f"Harvest of SMM modules using '{cls.__name__}' failed")
            continue
