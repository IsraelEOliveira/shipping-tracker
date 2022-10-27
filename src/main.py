import sys
from re import match
from json import dump
from driver import DriverService
from strategies.coscon import CosconTracker


if __name__ == '__main__':
  value = sys.argv[1] if len(sys.argv) > 0 else None

  if value is not None:
    cargo_pfx, cargo_number = match(r'([a-zA-Z]+)(\d+)', value).groups()

    # could create a metaclass for trackers
    # and identify their tracker by prefix
    # so this could be a factory instead of a
    # simple test condition
    if cargo_pfx != 'COSU':
      print(f'Warn: {cargo_pfx} doesnt look like a COSCO shipment')

    scraper = CosconTracker()
    result = scraper.lookup(cargo_pfx, cargo_number)

    with open(f'{value}.json', 'w') as save_file:
      dump(result, save_file, indent=2)
  else:
    print('Make sure to pass in the container no.')

  DriverService.shutdown()