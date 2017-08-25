# Collectd plugin for Cumulus switches (system)

This plugin collects data from `smonctl` and `ledmgrd` and exports
them to collectd. This includes temperature, fan status, PSU status
and front panel leds.

## Installation

The plugin should be copied in `/usr/share/collectd/python/` or
another place specified by `ModulePath` in the Python plugin
configuration. The `types.cumulus.db` file also needs to be copied in
`/usr/share/collectd/` and registered with `TypesDB`.

## Configuration

This should be used like this:

    LoadPlugin python
    TypesDB "/usr/share/collectd/types.cumulus.db"

    <Plugin python>
      ModulePath "/usr/share/collectd/python"
      Import "cumulus"
    </Plugin>

# Testing

A one-time collection can be triggered with:

    collectd -C collectd.conf -T
