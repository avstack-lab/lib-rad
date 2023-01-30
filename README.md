# Radar Sensor Utilities

Managing radar sensors with a flexible and standardized python library.

## Purpose

The purpose of this library is to standadize interfaces for radar sensors.
This will allow for better modularity of sensors in future hardware designs.
It will also support improved documentation and lower barrier to entry for using radars.

## Getting Started

The best way to get started is to check out the [unit tests](https://github.com/avstack-lab/lib-rad/tree/main/tests) -- even the commented-out ones.

This library is nascent. The most pressing needs are:
- Adding support for new sensors
- Defining application-specific configuration files
- Adding testing
- Improved playback and visualization
- Integrating with tracking libraries (outside the scope of this repository)

## Sensors Supported

### uRad Automotive

Find this radar [online][urad-radar]. This radar uses the Texas Instrument AWR1843AOP.
See the [uRad automotive datasheet][urad-datasheet] for more info.

[urad-radar]: https://urad.es/en/product/urad-radar-automotive
[urad-datasheet]: https://urad.es/wp-content/descargables/uRAD%20-%20Datasheet%20-%20Automotive%20v2.0%20-%20EN.pdf
