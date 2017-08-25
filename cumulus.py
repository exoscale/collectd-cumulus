#!/usr/bin/env python

"""Collectd module to extract statistics from Cumulus switches."""

from __future__ import print_function
from __future__ import unicode_literals

import json
import subprocess
import collectd


class Cumulus(object):

    def refresh(self):
        self.ledmgrd = json.loads(
            subprocess.check_output(["/usr/sbin/ledmgrd", "-j"]))
        self.smonctl = json.loads(
            subprocess.check_output(["/usr/sbin/smonctl", "-j"]))

    def get_fans(self):
        """Return memory information about fans.

        This information is collected from smonctl.

        """
        return [{"name": fan["name"],
                 "state": fan["state"],
                 "speed": dict(current=fan["input"],
                               min=fan["min"],
                               max=fan["max"],
                               variance=fan["var"])}
                for fan in self.smonctl
                if fan['type'] == "fan"]

    def get_psus(self):
        """Return memory information about PSUs.

        This information is collected from smonctl.

        """
        return [{"name": psu["name"],
                 "state": psu["state"]}
                for psu in self.smonctl
                if psu['type'] == "power"]

    def get_temps(self):
        """Return memory information about temperature sensors.

        This information is collected from smonctl.

        """
        return [{"name": temp["name"],
                 "state": temp["state"],
                 "min": temp["min"],
                 "max": temp["max"],
                 "crit": temp["crit"],
                 "current": temp["avg"]}
                for temp in self.smonctl
                if temp['type'] == "temp"]

    def get_leds(self):
        """Return memory information about front LEDs.

        This information is collected from ledmgrd.

        """
        return [{"name": led["name"],
                 "state": led["color"] == led["good_led_color"]
                 and "OK" or "NOK"}
                for led in self.ledmgrd]


class CumulusCollectd(object):

    def configure(self, conf, **kwargs):

        """Collectd configuration callback."""
        if conf is not None:
            kwargs.update({node.key.lower(): node.values
                           for node in conf.children})
        for keyword in kwargs:
            if not isinstance(kwargs[keyword], (list, tuple)):
                kwargs[keyword] = [kwargs[keyword]]
            raise ValueError("config: unknown keyword "
                             "`{}`".format(keyword))

    def init(self):
        """Collectd init callback."""
        self.cumulus = Cumulus()

    def dispatch(self, values, type, type_instance):
        """Dispatch a value to collectd."""
        if values is None or any([v is None for v in values]):
            return
        metric = collectd.Values(values=values,
                                 plugin="cumulus",
                                 type="cumulus_{}".format(type),
                                 type_instance=type_instance)
        metric.dispatch()

    def read(self):
        """Collectd read callback."""
        self.cumulus.refresh()

        # Fans
        fans = self.cumulus.get_fans()
        for fan in fans:
            speed = fan["speed"]
            self.dispatch([fan["state"] == "OK" and 1 or 0,
                           speed["current"],
                           speed["min"],
                           speed["max"],
                           speed["variance"]],
                          "fan", fan["name"].lower())
        # PSUs
        psus = self.cumulus.get_psus()
        for psu in psus:
            self.dispatch([psu["state"] == "OK" and 1 or 0],
                          "psu", psu["name"].lower())
        # Temperature sensors
        temps = self.cumulus.get_temps()
        for temp in temps:
            self.dispatch([temp["state"] == "OK" and 1 or 0,
                           temp["current"],
                           temp["min"],
                           temp["max"],
                           temp["crit"]],
                          "temp", temp["name"].lower())
        # LEDs
        leds = self.cumulus.get_leds()
        for led in leds:
            self.dispatch([led["state"] == "OK" and 1 or 0],
                          "led", led["name"].lower())


cumulus = CumulusCollectd()
collectd.register_config(cumulus.configure)
collectd.register_init(cumulus.init)
collectd.register_read(cumulus.read)
