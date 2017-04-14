# -*- coding: utf-8 -*-

import math
from random import random

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPolygonF, QPen, QBrush

from . import util


class BoidSim(object):
    # TODO: teams
    # TODO: obstacles

    def __init__(self, scene, bounds_radius):
        self.scene = scene
        self.bounds_radius = bounds_radius
        self.boids = set()
        for _ in range(100):
            pr = random() * bounds_radius
            pt = random() * math.pi * 2
            vr = Boid.speed
            vt = random() * math.pi * 2
            self.boids.add(Boid(self,
                QPointF(pr * math.cos(pt), pr * math.sin(pt)),
                QPointF(vr * math.cos(vt), vr * math.sin(vt))))

    def update(self, dt):
        for boid in self.boids:
            boid.acceleration = QPointF()

            bounds_repel = util.lerp(util.length(boid.position), self.bounds_radius * 0.9, self.bounds_radius, 0, 2000, True) * -util.normalized_or_null(boid.position)
            boid.acceleration += bounds_repel

            boid.neighborhood = set(neighbor for neighbor in self.boids if neighbor is not boid and util.lengthsq(neighbor.position - boid.position) < boid.visual_range * boid.visual_range)
            if boid.neighborhood:
                separation = sum((boid.position - neighbor.position for neighbor in boid.neighborhood), QPointF())
                boid.acceleration += separation / 40 * 60

                avg_heading = sum((neighbor.velocity for neighbor in boid.neighborhood), QPointF()) / len(boid.neighborhood)
                alignment = avg_heading - boid.velocity
                boid.acceleration += alignment / 8 * 60

                avg_position = sum((neighbor.position for neighbor in boid.neighborhood), QPointF()) / len(boid.neighborhood)
                cohesion = avg_position - boid.position
                boid.acceleration += cohesion / 100 * 60

        for boid in self.boids:
            boid.update(dt)

class Boid(object):
    speed = 100
    visual_range = 50

    def __init__(self, sim, position, velocity):
        self.sim = sim

        self.position = position
        self.velocity = velocity

        self.body_graphic = sim.scene.addPolygon(
            QPolygonF([
                QPointF(1, 0),
                QPointF(-0.6, 0.6),
                QPointF(-0.3, 0),
                QPointF(-0.6, -0.6)]),
            QPen(Qt.NoPen),
            QBrush(util.hsl(0, 90, 80)))
        self.body_graphic.setScale(10)

        self.visual_range_graphic = sim.scene.addEllipse(
            -self.visual_range, -self.visual_range,
            self.visual_range * 2, self.visual_range * 2,
            QPen(util.hsl(0, 0, 0, 20)),
            QBrush())
        self.visual_range_graphic.setVisible(False)

        self.graphics_group = sim.scene.createItemGroup([
            self.body_graphic,
            self.visual_range_graphic])

        self._update_graphics()

    def _update_graphics(self):
        self.graphics_group.setX(self.position.x())
        self.graphics_group.setY(self.position.y())
        self.body_graphic.setRotation(util.rad2deg(math.atan2(self.velocity.y(), self.velocity.x())))

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.velocity = util.normalized(self.velocity) * self.speed

        self.position += self.velocity * dt
        if util.lengthsq(self.position) > self.sim.bounds_radius * self.sim.bounds_radius:
            self.position /= util.length(self.position)
            self.velocity = self.velocity - 2 * QPointF.dotProduct(self.velocity, self.position) * self.position
            self.position *= self.sim.bounds_radius

        self._update_graphics()
