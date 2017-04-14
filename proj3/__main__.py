# -*- coding: utf-8 -*-

import sys
import math
import itertools

from PyQt5.QtGui import QPen, QBrush
from PyQt5.QtWidgets import QApplication

from .animation import Animation
from .boids import BoidSim
from . import util


class Proj3Ani(Animation):
    """
    Implements the kinematics animation.
    """

    def __init__(self):
        super().__init__(
            title='CS 4732 Project 3 by Daniel Beckwith',
            frame_rate=60.0,
            run_time=60.0)

        # set view size
        self.view.resize(800, 800)
        self.setup_scene(
            background_color=util.hsl(0, 0, 100))

    def make_scene(self):
        """
        Overriddes Animation.make_scene
        """
        # create boid sim
        # pick bounds radius to fit inside view
        self.sim = BoidSim(self.scene, min(self.view.width(), self.view.height()) / 2)

    def update(self, frame, t, dt):
        """
        Overriddes Animation.update
        """
        # just update boid sim
        self.sim.update(dt)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        prog='proj3',
        description='Boids simulation',
        epilog='Created by Daniel Beckwith for WPI CS 4732.')
    args = parser.parse_args()

    app = QApplication([])

    ani = Proj3Ani()
    ani.run()

    sys.exit(app.exec_())
